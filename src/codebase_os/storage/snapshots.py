from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol

import httpx

from ..config import Settings


@dataclass(frozen=True)
class SnapshotObject:
    path: str
    content: bytes
    content_type: str
    metadata: dict[str, str]


class SnapshotStore(Protocol):
    def put(self, tenant_id: str, repository_id: str, commit: str, content: bytes) -> SnapshotObject: ...
    def get(self, tenant_id: str, repository_id: str, commit: str) -> bytes: ...
    def delete(self, tenant_id: str, repository_id: str, commit: str) -> None: ...


def snapshot_path(tenant_id: str, repository_id: str, commit: str) -> str:
    if not tenant_id or not re.fullmatch(r"[A-Za-z0-9._-]+", tenant_id):
        raise ValueError("snapshot identifiers must be path-safe")
    repository_parts = repository_id.split("/")
    if any(not part or not re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in repository_parts):
        raise ValueError("snapshot identifiers must be path-safe")
    if not commit or not re.fullmatch(r"[A-Za-z0-9._-]+", commit):
        raise ValueError("snapshot identifiers must be path-safe")
    return f"tenants/{tenant_id}/repositories/{'/'.join(repository_parts)}/{commit}.snapshot"


class InMemorySnapshotStore:
    def __init__(self) -> None:
        self.objects: dict[str, SnapshotObject] = {}

    def put(self, tenant_id: str, repository_id: str, commit: str, content: bytes) -> SnapshotObject:
        path = snapshot_path(tenant_id, repository_id, commit)
        value = SnapshotObject(path, content, "application/json", {"tenant_id": tenant_id, "commit": commit})
        self.objects[path] = value
        return value

    def get(self, tenant_id: str, repository_id: str, commit: str) -> bytes:
        return self.objects[snapshot_path(tenant_id, repository_id, commit)].content

    def delete(self, tenant_id: str, repository_id: str, commit: str) -> None:
        self.objects.pop(snapshot_path(tenant_id, repository_id, commit), None)


class SupabaseSnapshotStore:
    def __init__(self, project_url: str, bucket: str, server_key: str, transport=None) -> None:
        self.bucket = bucket
        self.base_url = project_url.rstrip("/") + "/storage/v1"
        self.client = httpx.Client(transport=transport, timeout=20.0)
        self.headers = {"authorization": f"Bearer {server_key}", "apikey": server_key}

    def put(self, tenant_id: str, repository_id: str, commit: str, content: bytes) -> SnapshotObject:
        path = snapshot_path(tenant_id, repository_id, commit)
        response = self.client.post(
            f"{self.base_url}/object/{self.bucket}/{path}",
            headers={**self.headers, "content-type": "application/octet-stream", "x-upsert": "true"},
            content=content,
        )
        self._check(response)
        return SnapshotObject(path, content, "application/octet-stream", {"tenant_id": tenant_id, "commit": commit})

    def get(self, tenant_id: str, repository_id: str, commit: str) -> bytes:
        response = self.client.get(f"{self.base_url}/object/{self.bucket}/{snapshot_path(tenant_id, repository_id, commit)}", headers=self.headers)
        self._check(response)
        return response.content

    def delete(self, tenant_id: str, repository_id: str, commit: str) -> None:
        response = self.client.delete(f"{self.base_url}/object/{self.bucket}/{snapshot_path(tenant_id, repository_id, commit)}", headers=self.headers)
        self._check(response)

    @staticmethod
    def _check(response: httpx.Response) -> None:
        if response.status_code >= 400:
            raise RuntimeError(f"snapshot storage request failed with status {response.status_code}")


def build_snapshot_store(settings: Settings) -> SnapshotStore:
    if settings.object_storage_provider == "local":
        return InMemorySnapshotStore()
    if settings.object_storage_provider != "supabase" or not settings.supabase_url:
        raise ValueError("Supabase snapshot storage requires a project URL")
    if settings.object_storage_secret_key is None:
        if settings.environment != "production":
            return InMemorySnapshotStore()
        raise ValueError("Supabase snapshot storage requires a server key")
    return SupabaseSnapshotStore(
        settings.supabase_url,
        settings.object_storage_bucket,
        settings.object_storage_secret_key.get_secret_value(),
    )
