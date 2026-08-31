from dataclasses import dataclass
from typing import Protocol

from .webhooks import affected_repository_ids


class GitHubClient(Protocol):
    def installation_repositories(self, installation_id: int) -> list[dict]: ...
    def repository_snapshot(self, full_name: str, branch: str) -> object: ...


@dataclass(frozen=True)
class GitHubInstallation:
    installation_id: int
    repositories: tuple[str, ...]


class GitHubProvider:
    def __init__(self, client: GitHubClient) -> None:
        self.client = client

    def installation(self, installation_id: int) -> GitHubInstallation:
        repositories = self.client.installation_repositories(installation_id)
        names = tuple(sorted(item["full_name"] for item in repositories if isinstance(item.get("full_name"), str)))
        return GitHubInstallation(installation_id, names)

    def repositories_for_event(self, payload: dict) -> list[str]:
        return affected_repository_ids(payload)

