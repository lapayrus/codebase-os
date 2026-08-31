import hashlib
import hmac
import json


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

