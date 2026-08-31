import hashlib
import hmac
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class IngestionJob:
    delivery_id: str
    installation_id: int
    repository_id: str
    event_name: str


class IngestionJobQueue:
    def __init__(self) -> None:
        self.jobs: list[IngestionJob] = []
        self._deliveries: set[tuple[str, str]] = set()

    def enqueue(self, job: IngestionJob) -> bool:
        key = (job.delivery_id, job.repository_id)
        if key in self._deliveries:
            return False
        self._deliveries.add(key)
        self.jobs.append(job)
        return True


class InstallationAccess:
    def __init__(self) -> None:
        self._repositories: dict[int, set[str]] = {}

    def grant(self, installation_id: int, repositories: list[str]) -> None:
        self._repositories[installation_id] = set(repositories)

    def allowed(self, installation_id: int, repository_id: str) -> bool:
        return repository_id in self._repositories.get(installation_id, set())

    def revoke(self, installation_id: int) -> None:
        self._repositories.pop(installation_id, None)


def verify_signature(body: bytes, signature: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def parse_event(body: bytes, event_name: str) -> dict:
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("GitHub webhook payload must be an object")
    payload["event_name"] = event_name
    return payload


def affected_repository_ids(payload: dict) -> list[str]:
    repository = payload.get("repository") or {}
    full_name = repository.get("full_name")
    return [full_name] if isinstance(full_name, str) and full_name else []


class GitHubWebhookProcessor:
    def __init__(self, secret: str, queue: IngestionJobQueue, access: InstallationAccess) -> None:
        self.secret = secret
        self.queue = queue
        self.access = access

    def handle(
        self,
        body: bytes,
        signature: str,
        event_name: str,
        delivery_id: str,
        action: str | None = None,
    ) -> dict[str, int]:
        if not verify_signature(body, signature, self.secret):
            raise PermissionError("Invalid GitHub webhook signature")
        payload = parse_event(body, event_name)
        action = action or payload.get("action")
        installation_id = (payload.get("installation") or {}).get("id")
        if not isinstance(installation_id, int):
            return {"queued": 0}
        if event_name == "installation" and action == "deleted":
            self.access.revoke(installation_id)
            return {"queued": 0}
        repository_ids = affected_repository_ids(payload)
        if event_name == "installation" and action in {"created", "added"}:
            repository_ids = [
                item.get("full_name")
                for item in payload.get("repositories", [])
                if isinstance(item, dict) and isinstance(item.get("full_name"), str)
            ]
            self.access.grant(installation_id, repository_ids)
            queued = sum(
                self.queue.enqueue(IngestionJob(delivery_id, installation_id, repository_id, "installation"))
                for repository_id in repository_ids
            )
            return {"queued": queued}
        queued = 0
        for repository_id in repository_ids:
            if self.access.allowed(installation_id, repository_id):
                queued += self.queue.enqueue(IngestionJob(delivery_id, installation_id, repository_id, event_name))
        return {"queued": queued}
