import hashlib
import hmac
import json
from codebase_os.providers.webhooks import (
    GitHubWebhookProcessor,
    IngestionJobQueue,
    InstallationAccess,
    parse_event,
    verify_signature,
)


def test_webhook_signature_uses_sha256_hmac():
    body = b'{"repository":{"full_name":"acme/demo"}}'
    secret = "secret"
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(body, signature, secret)
    assert not verify_signature(body, signature + "x", secret)


def test_parse_event_adds_event_name():
    payload = parse_event(json.dumps({"repository": {"full_name": "acme/demo"}}).encode(), "push")
    assert payload["event_name"] == "push"


def test_valid_push_enqueues_once_per_delivery():
    body = json.dumps({
        "installation": {"id": 42},
        "repository": {"full_name": "acme/demo"},
    }).encode()
    secret = "secret"
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    queue = IngestionJobQueue()
    access = InstallationAccess()
    access.grant(42, ["acme/demo"])
    processor = GitHubWebhookProcessor(secret, queue, access)

    assert processor.handle(body, signature, "push", "delivery-1") == {"queued": 1}
    assert processor.handle(body, signature, "push", "delivery-1") == {"queued": 0}
    assert queue.jobs[0].repository_id == "acme/demo"


def test_deleted_installation_removes_repository_access():
    body = json.dumps({"installation": {"id": 42}}).encode()
    secret = "secret"
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    access = InstallationAccess()
    access.grant(42, ["acme/demo"])
    processor = GitHubWebhookProcessor(secret, IngestionJobQueue(), access)

    assert processor.handle(body, signature, "installation", "delivery-2", action="deleted") == {"queued": 0}
    assert not access.allowed(42, "acme/demo")


def test_installation_created_grants_and_queues_each_visible_repository():
    body = json.dumps({
        "installation": {"id": 42},
        "repositories": [{"full_name": "acme/a"}, {"full_name": "acme/b"}],
        "action": "created",
    }).encode()
    secret = "secret"
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    queue = IngestionJobQueue()
    access = InstallationAccess()

    assert GitHubWebhookProcessor(secret, queue, access).handle(body, signature, "installation", "delivery-3") == {"queued": 2}
    assert [job.repository_id for job in queue.jobs] == ["acme/a", "acme/b"]
