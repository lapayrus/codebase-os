from enum import Enum
import hashlib
import json


class IndexDecision(str, Enum):
    UNCHANGED = "unchanged"
    REINDEX = "reindex"
    RETRY = "retry"


def file_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def content_version(files: dict[str, str]) -> str:
    payload = [(path, file_hash(files[path])) for path in sorted(files)]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest()


def decide_index(current_version: str | None, incoming_version: str, status: str | None) -> IndexDecision:
    if status == "failed":
        return IndexDecision.RETRY
    if current_version == incoming_version and status == "succeeded":
        return IndexDecision.UNCHANGED
    return IndexDecision.REINDEX
