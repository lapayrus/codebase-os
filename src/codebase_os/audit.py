from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


@dataclass(frozen=True)
class AuditEvent:
    id: str
    tenant_id: str
    user_id: str
    action: str
    repository: str | None
    request_id: str
    created_at: datetime


class AuditLog:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, tenant_id: str, user_id: str, action: str, repository: str | None, request_id: str) -> AuditEvent:
        event = AuditEvent(str(uuid.uuid4()), tenant_id, user_id, action, repository, request_id, datetime.now(timezone.utc))
        self.events.append(event)
        return event

