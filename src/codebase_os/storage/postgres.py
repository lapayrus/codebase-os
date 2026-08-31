SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS repositories (
    tenant_id TEXT NOT NULL, id TEXT NOT NULL, name TEXT NOT NULL, provider TEXT NOT NULL,
    branch TEXT NOT NULL, commit TEXT NOT NULL, indexed_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant_id, id)
);
CREATE TABLE IF NOT EXISTS evidence (
    tenant_id TEXT NOT NULL, id TEXT NOT NULL, repository_id TEXT NOT NULL, commit TEXT NOT NULL,
    path TEXT NOT NULL, start_line INTEGER NOT NULL, end_line INTEGER NOT NULL, snippet TEXT NOT NULL,
    kind TEXT NOT NULL, PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, repository_id) REFERENCES repositories(tenant_id, id)
);
CREATE TABLE IF NOT EXISTS memories (
    tenant_id TEXT NOT NULL, id TEXT NOT NULL, repository_id TEXT NOT NULL, text TEXT NOT NULL,
    memory_type TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL, stale BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (tenant_id, id), FOREIGN KEY (tenant_id, repository_id) REFERENCES repositories(tenant_id, id)
);
CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, action TEXT NOT NULL, repository_id TEXT,
    request_id TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL
);
"""


class PostgresStore:
    def __init__(self, connection) -> None:
        self.connection = connection

    def initialize(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(SCHEMA_SQL)
        self.connection.commit()

    def save_repository(self, tenant_id, repository) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO repositories (tenant_id,id,name,provider,branch,commit,indexed_at) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id,id) DO UPDATE SET name=EXCLUDED.name, commit=EXCLUDED.commit, indexed_at=EXCLUDED.indexed_at", (tenant_id, repository.id, repository.name, repository.provider, repository.branch, repository.commit, repository.indexed_at))
        self.connection.commit()

    def get_repository(self, tenant_id, repository_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT id,name,provider,branch,commit,indexed_at FROM repositories WHERE tenant_id=%s AND id=%s", (tenant_id, repository_id))
            row = cursor.fetchone()
        if not row:
            return None
        return self._repository(repository_id, row)

    def list_repositories(self, tenant_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT id,name,provider,branch,commit,indexed_at FROM repositories WHERE tenant_id=%s ORDER BY id", (tenant_id,))
            rows = cursor.fetchall()
        return [self._repository(row[0], row) for row in rows]

    def save_evidence(self, tenant_id, evidence) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO evidence (tenant_id,id,repository_id,commit,path,start_line,end_line,snippet,kind) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id,id) DO NOTHING", (tenant_id, evidence.id, evidence.repository_id, evidence.commit, evidence.path, evidence.start_line, evidence.end_line, evidence.snippet, evidence.kind))
        self.connection.commit()

    def list_evidence(self, tenant_id, repository_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT id,repository_id,commit,path,start_line,end_line,snippet,kind FROM evidence WHERE tenant_id=%s AND repository_id=%s ORDER BY id", (tenant_id, repository_id))
            rows = cursor.fetchall()
        return [self._evidence(row) for row in rows]

    def save_memory(self, tenant_id, memory) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO memories (tenant_id,id,repository_id,text,memory_type,created_at,stale) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id,id) DO NOTHING", (tenant_id, memory.id, memory.repository_id, memory.text, memory.memory_type, memory.created_at, memory.stale))
        self.connection.commit()

    def list_memories(self, tenant_id, repository_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT id,repository_id,text,memory_type,created_at,stale FROM memories WHERE tenant_id=%s AND repository_id=%s ORDER BY id", (tenant_id, repository_id))
            rows = cursor.fetchall()
        return [self._memory(row) for row in rows]

    @staticmethod
    def _repository(repository_id, row):
        from .records import RepositoryRecord
        return RepositoryRecord(repository_id, row[1], row[2], row[3], row[4], row[5])

    @staticmethod
    def _evidence(row):
        from .records import EvidenceRecord
        return EvidenceRecord(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])

    @staticmethod
    def _memory(row):
        from .records import MemoryRecord
        return MemoryRecord(row[0], row[1], row[2], row[3], row[4], row[5])
