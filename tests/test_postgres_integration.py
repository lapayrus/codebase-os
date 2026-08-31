import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from codebase_os.config import Settings
from codebase_os.runtime import build_storage, initialize_storage
from codebase_os.storage.records import RepositoryRecord

pytestmark = pytest.mark.integration


def test_repository_survives_store_recreation():
    database_url = os.getenv("CODEBASEOS_DATABASE_URL", "postgresql://postgres@127.0.0.1:5432/codebaseos")
    repository_id = f"phase1-restart-{uuid4().hex}"
    settings = Settings(database_url=database_url)
    repository = RepositoryRecord(
        repository_id,
        repository_id,
        "local",
        "main",
        "phase1-commit",
        datetime.now(timezone.utc),
    )

    first = build_storage(settings)
    initialize_storage(first)
    first.save_repository("phase1-test", repository)

    second = build_storage(settings)
    try:
        assert second.get_repository("phase1-test", repository_id) is not None
    finally:
        second.delete_repository("phase1-test", repository_id)
