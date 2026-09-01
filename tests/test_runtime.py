import pytest

from codebase_os.config import Settings
from codebase_os.storage.postgres import PostgresStore
from codebase_os.runtime import build_storage, initialize_storage


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=None):
        self.connection.executed_schema = query.lstrip().startswith("CREATE TABLE")


class FakeConnection:
    def __init__(self):
        self.committed = False
        self.executed_schema = False
        self.client_encoding = None

    def cursor(self):
        return FakeCursor(self)

    def execute(self, query):
        self.client_encoding = query

    def commit(self):
        self.committed = True


def raise_error(_):
    raise OSError("password=secret connection refused")


def test_build_storage_uses_postgres_for_postgresql_url():
    settings = Settings(database_url="postgresql://user:pass@localhost/codebaseos")
    fake_connection = object()

    storage = build_storage(settings, connector=lambda _: fake_connection)

    assert isinstance(storage, PostgresStore)
    assert storage.connection is fake_connection


def test_build_storage_rejects_sqlite_in_production():
    settings = Settings(environment="production", database_url="sqlite:///./codebaseos.db")

    with pytest.raises(ValueError, match="production requires PostgreSQL"):
        build_storage(settings, connector=lambda _: object())


def test_initialize_storage_creates_schema_before_serving():
    connection = FakeConnection()
    storage = build_storage(
        Settings(database_url="postgresql://user:pass@localhost/codebaseos"),
        connector=lambda _: connection,
    )

    initialize_storage(storage)

    assert connection.committed is True
    assert connection.executed_schema is True
    assert connection.client_encoding == "SET client_encoding TO 'UTF8'"


def test_connection_failure_is_redacted():
    with pytest.raises(RuntimeError, match="database connection failed") as error:
        build_storage(
            Settings(database_url="postgresql://user:secret@localhost/db"),
            connector=raise_error,
        )

    assert "secret" not in str(error.value)
