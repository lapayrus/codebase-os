from collections.abc import Callable

import psycopg

from .config import Settings
from .storage.memory import InMemoryStore
from .storage.ports import Storage
from .storage.postgres import PostgresStore


def build_storage(
    settings: Settings,
    connector: Callable[[str], object] = psycopg.connect,
) -> Storage:
    database_url = settings.database_url.strip()
    if database_url.startswith(("postgresql://", "postgres://")):
        try:
            return PostgresStore(connector(database_url))
        except Exception as exc:
            raise RuntimeError("database connection failed") from exc
    if settings.environment == "production":
        raise ValueError("production requires PostgreSQL")
    if database_url.startswith("sqlite://"):
        return InMemoryStore()
    raise ValueError("unsupported database URL")


def initialize_storage(storage: Storage) -> None:
    if isinstance(storage, PostgresStore):
        try:
            storage.initialize()
        except Exception as exc:
            raise RuntimeError("database initialization failed") from exc
