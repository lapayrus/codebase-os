import hashlib
import hmac
import json
from codebase_os.providers.webhooks import parse_event, verify_signature


def test_webhook_signature_uses_sha256_hmac():
    body = b'{"repository":{"full_name":"acme/demo"}}'
    secret = "secret"
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(body, signature, secret)
    assert not verify_signature(body, signature + "x", secret)


def test_parse_event_adds_event_name():
    payload = parse_event(json.dumps({"repository": {"full_name": "acme/demo"}}).encode(), "push")
    assert payload["event_name"] == "push"

