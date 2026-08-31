from datetime import datetime, timedelta, timezone


def retained(created_at: datetime, retention_days: int, now: datetime | None = None) -> bool:
    reference = now or datetime.now(timezone.utc)
    return created_at >= reference - timedelta(days=retention_days)


def purge_ids(items: list[tuple[str, datetime]], retention_days: int, now: datetime | None = None) -> list[str]:
    reference = now or datetime.now(timezone.utc)
    cutoff = reference - timedelta(days=retention_days)
    return [item_id for item_id, created_at in items if created_at < cutoff]

