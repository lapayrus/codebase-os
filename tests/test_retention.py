from datetime import datetime, timedelta, timezone
from codebase_os.retention import purge_ids, retained


def test_retention_keeps_recent_items():
    now = datetime.now(timezone.utc)
    assert retained(now - timedelta(days=2), 7, now)
    assert not retained(now - timedelta(days=8), 7, now)


def test_purge_ids_returns_only_expired_items():
    now = datetime.now(timezone.utc)
    items = [("recent", now - timedelta(days=2)), ("old", now - timedelta(days=8))]
    assert purge_ids(items, 7, now) == ["old"]

