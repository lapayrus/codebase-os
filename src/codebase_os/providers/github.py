import base64
import time
from dataclasses import dataclass
from typing import Protocol

import httpx
import jwt

from ..indexer import RepositoryIndex
from ..config import Settings
from ..persistence import PersistentCodebaseService
from .webhooks import affected_repository_ids


def create_app_jwt(app_id: str, private_key: str, now: int | None = None) -> str:
    issued_at = now or int(time.time())
    return jwt.encode(
        {"iat": issued_at - 60, "exp": issued_at + 540, "iss": app_id},
        private_key,
        algorithm="RS256",
    )


def build_github_client(settings: Settings, installation_id: int | None = None) -> "GitHubHttpClient":
    if not settings.github_app_id or not settings.github_private_key:
        raise ValueError("GitHub App credentials are not configured")
    return GitHubHttpClient(
        create_app_jwt(settings.github_app_id, settings.github_private_key.get_secret_value()),
        api_url=settings.github_api_url,
        installation_id=installation_id,
        retries=settings.github_retry_count,
        timeout=settings.github_request_timeout,
    )


class GitHubClient(Protocol):
    def installation_token(self, installation_id: int) -> str: ...
    def installation_repositories(self, installation_id: int) -> list[dict]: ...
    def repository_snapshot(self, full_name: str, branch: str) -> object: ...


@dataclass(frozen=True)
class GitHubInstallation:
    installation_id: int
    repositories: tuple[str, ...]
    source_permissions: tuple[str, ...] = ()


class GitHubProvider:
    def __init__(self, client: GitHubClient) -> None:
        self.client = client

    def installation(self, installation_id: int) -> GitHubInstallation:
        repositories = self.client.installation_repositories(installation_id)
        names = tuple(sorted(item["full_name"] for item in repositories if isinstance(item.get("full_name"), str)))
        permissions = tuple(
            f"{item['full_name']}:{','.join(f'{key}={value}' for key, value in sorted(item.get('permissions', {}).items()))}"
            for item in repositories
            if isinstance(item.get("full_name"), str) and isinstance(item.get("permissions"), dict)
        )
        return GitHubInstallation(installation_id, names, tuple(sorted(permissions)))

    def installation_token(self, installation_id: int) -> str:
        return self.client.installation_token(installation_id)


class GitHubHttpClient:
    def __init__(
        self,
        app_token: str,
        api_url: str = "https://api.github.com",
        installation_id: int | None = None,
        transport: httpx.BaseTransport | None = None,
        retries: int = 2,
        timeout: float = 15.0,
    ) -> None:
        self.app_token = app_token
        self.api_url = api_url.rstrip("/")
        self.installation_id = installation_id
        self.retries = retries
        self.client = httpx.Client(transport=transport, timeout=timeout)

    def installation_token(self, installation_id: int) -> str:
        response = self._request(
            "POST",
            f"/app/installations/{installation_id}/access_tokens",
            app_auth=True,
        )
        return response.json()["token"]

    def app_installations(self) -> list[dict]:
        return self._request("GET", "/app/installations", app_auth=True).json()

    def installation_repositories(self, installation_id: int) -> list[dict]:
        token = self.installation_token(installation_id)
        repositories = []
        page = 1
        while True:
            response = self._request(
                "GET",
                f"/installation/repositories?installation_id={installation_id}&per_page=100&page={page}",
                token=token,
            )
            batch = response.json().get("repositories", [])
            repositories.extend(batch)
            if len(batch) < 100:
                return repositories
            page += 1

    def repository_snapshot(self, full_name: str, branch: str) -> RepositoryIndex:
        if self.installation_id is None:
            raise RuntimeError("installation id is required for snapshot access")
        token = self.installation_token(self.installation_id)
        metadata = self._request("GET", f"/repos/{full_name}", token=token).json()
        resolved_branch = branch or metadata["default_branch"]
        ref = self._request(
            "GET", f"/repos/{full_name}/git/refs/heads/{resolved_branch}", token=token
        ).json()
        commit = ref["object"]["sha"]
        tree = self._request("GET", f"/repos/{full_name}/git/trees/{commit}?recursive=1", token=token).json()
        files = {}
        for item in tree.get("tree", []):
            if item.get("type") != "blob" or item.get("size", 0) > 1_000_000:
                continue
            content = self._request("GET", f"/repos/{full_name}/git/blobs/{item['sha']}", token=token).json()
            if content.get("encoding") != "base64":
                continue
            try:
                files[item["path"]] = base64.b64decode(content["content"]).decode("utf-8")
            except (UnicodeDecodeError, ValueError):
                continue
        return RepositoryIndex(full_name, "", commit, files)

    def _request(self, method: str, path: str, token: str | None = None, app_auth: bool = False) -> httpx.Response:
        headers = {"accept": "application/vnd.github+json"}
        if app_auth:
            headers["authorization"] = f"Bearer {self.app_token}"
        elif token:
            headers["authorization"] = f"token {token}"
        for attempt in range(self.retries + 1):
            response = self.client.request(method, f"{self.api_url}{path}", headers=headers)
            if response.status_code == 429 or response.status_code == 403 and response.headers.get("x-ratelimit-remaining") == "0":
                if attempt < self.retries:
                    time.sleep(0.01)
                    continue
            if response.status_code >= 500 and attempt < self.retries:
                time.sleep(0.01)
                continue
            if response.status_code >= 400:
                raise RuntimeError(f"GitHub request failed with status {response.status_code}")
            return response
        raise RuntimeError("GitHub request retries exhausted")


class GitHubIngestionWorker:
    def __init__(self, queue, client: GitHubClient, service: PersistentCodebaseService) -> None:
        self.queue = queue
        self.client = client
        self.service = service

    def run_once(self, tenant_id: str) -> bool:
        job = self.queue.claim()
        if job is None:
            return False
        try:
            snapshot = self.client.repository_snapshot(job.repository_id, "")
            self.service.index_repository(snapshot, tenant_id)
        except Exception:
            self.queue.fail(job.delivery_id, job.repository_id)
            raise
        self.queue.complete(job.delivery_id, job.repository_id)
        return True

    def repositories_for_event(self, payload: dict) -> list[str]:
        return affected_repository_ids(payload)
