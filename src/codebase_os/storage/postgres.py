SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS repositories (
    tenant_id TEXT NOT NULL, id TEXT NOT NULL, name TEXT NOT NULL, provider TEXT NOT NULL,
    branch TEXT NOT NULL, commit TEXT NOT NULL, indexed_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant_id, id)
);
ALTER TABLE repositories ADD COLUMN IF NOT EXISTS indexing_status TEXT NOT NULL DEFAULT 'succeeded';
ALTER TABLE repositories ADD COLUMN IF NOT EXISTS content_version TEXT;
CREATE TABLE IF NOT EXISTS evidence (
    tenant_id TEXT NOT NULL, id TEXT NOT NULL, repository_id TEXT NOT NULL, commit TEXT NOT NULL,
    path TEXT NOT NULL, start_line INTEGER NOT NULL, end_line INTEGER NOT NULL, snippet TEXT NOT NULL,
    kind TEXT NOT NULL, PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, repository_id) REFERENCES repositories(tenant_id, id)
);
ALTER TABLE evidence ADD COLUMN IF NOT EXISTS file_hash TEXT;
CREATE TABLE IF NOT EXISTS memories (
    tenant_id TEXT NOT NULL, id TEXT NOT NULL, repository_id TEXT NOT NULL, text TEXT NOT NULL,
    memory_type TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL, stale BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (tenant_id, id), FOREIGN KEY (tenant_id, repository_id) REFERENCES repositories(tenant_id, id)
);
CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, action TEXT NOT NULL, repository_id TEXT,
    request_id TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS ingestion_jobs (
delivery_id TEXT NOT NULL, repository_id TEXT NOT NULL, installation_id BIGINT NOT NULL,
event_name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0,
lease_until TIMESTAMPTZ, last_error TEXT,
PRIMARY KEY (delivery_id, repository_id)
);
ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS lease_until TIMESTAMPTZ;
ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS last_error TEXT;
"""


class PostgresStore:
    def __init__(self, connection) -> None:
        self.connection = connection

    def initialize(self) -> None:
        if hasattr(self.connection, "execute"):
            self.connection.execute("SET client_encoding TO 'UTF8'")
        with self.connection.cursor() as cursor:
            cursor.execute(SCHEMA_SQL)
        self.connection.commit()

    def save_repository(self, tenant_id, repository) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO repositories (tenant_id,id,name,provider,branch,commit,indexed_at,indexing_status,content_version) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id,id) DO UPDATE SET name=EXCLUDED.name, commit=EXCLUDED.commit, indexed_at=EXCLUDED.indexed_at, indexing_status=EXCLUDED.indexing_status, content_version=EXCLUDED.content_version", (tenant_id, repository.id, repository.name, repository.provider, repository.branch, repository.commit, repository.indexed_at, repository.indexing_status, repository.content_version))
        self.connection.commit()

    def get_repository(self, tenant_id, repository_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT id,name,provider,branch,commit,indexed_at,indexing_status,content_version FROM repositories WHERE tenant_id=%s AND id=%s", (tenant_id, repository_id))
            row = cursor.fetchone()
        if not row:
            return None
        return self._repository(repository_id, row)

    def delete_repository(self, tenant_id, repository_id):
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM evidence WHERE tenant_id=%s AND repository_id=%s", (tenant_id, repository_id))
            cursor.execute("DELETE FROM memories WHERE tenant_id=%s AND repository_id=%s", (tenant_id, repository_id))
            cursor.execute("DELETE FROM audit_events WHERE tenant_id=%s AND repository_id=%s", (tenant_id, repository_id))
            cursor.execute("DELETE FROM repositories WHERE tenant_id=%s AND id=%s", (tenant_id, repository_id))
            deleted = cursor.rowcount > 0
        self.connection.commit()
        return deleted

    def list_repositories(self, tenant_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT id,name,provider,branch,commit,indexed_at,indexing_status,content_version FROM repositories WHERE tenant_id=%s ORDER BY id", (tenant_id,))
            rows = cursor.fetchall()
        return [self._repository(row[0], row) for row in rows]

    def save_evidence(self, tenant_id, evidence) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO evidence (tenant_id,id,repository_id,commit,path,start_line,end_line,snippet,kind,file_hash) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id,id) DO NOTHING", (tenant_id, evidence.id, evidence.repository_id, evidence.commit, evidence.path, evidence.start_line, evidence.end_line, evidence.snippet, evidence.kind, evidence.file_hash))
        self.connection.commit()

    def list_evidence(self, tenant_id, repository_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT id,repository_id,commit,path,start_line,end_line,snippet,kind,file_hash FROM evidence WHERE tenant_id=%s AND repository_id=%s ORDER BY id", (tenant_id, repository_id))
            rows = cursor.fetchall()
        return [self._evidence(row) for row in rows]

    def delete_evidence_except_commit(self, tenant_id, repository_id, commit):
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM evidence WHERE tenant_id=%s AND repository_id=%s AND commit<>%s", (tenant_id, repository_id, commit))
        self.connection.commit()

    def save_memory(self, tenant_id, memory) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO memories (tenant_id,id,repository_id,text,memory_type,created_at,stale) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id,id) DO NOTHING", (tenant_id, memory.id, memory.repository_id, memory.text, memory.memory_type, memory.created_at, memory.stale))
        self.connection.commit()

    def list_memories(self, tenant_id, repository_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT id,repository_id,text,memory_type,created_at,stale FROM memories WHERE tenant_id=%s AND repository_id=%s ORDER BY id", (tenant_id, repository_id))
            rows = cursor.fetchall()
        return [self._memory(row) for row in rows]

    def enqueue_ingestion_job(self, job) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO ingestion_jobs (delivery_id,repository_id,installation_id,event_name) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (job.delivery_id, job.repository_id, job.installation_id, job.event_name),
            )
            inserted = cursor.rowcount == 1
        self.connection.commit()
        return inserted

    def claim_ingestion_job(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT delivery_id,installation_id,repository_id,event_name,attempts FROM ingestion_jobs WHERE status IN ('queued','failed') OR (status='running' AND lease_until < NOW()) ORDER BY delivery_id FOR UPDATE SKIP LOCKED LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE ingestion_jobs SET status='running', attempts=attempts+1, lease_until=NOW() + INTERVAL '5 minutes' WHERE delivery_id=%s AND repository_id=%s",
                    (row[0], row[2]),
                )
        self.connection.commit()
        if not row:
            return None
        from ..providers.webhooks import IngestionJob

        return IngestionJob(row[0], row[1], row[2], row[3], row[4] + 1)

    def complete_ingestion_job(self, delivery_id: str, repository_id: str) -> None:
        self._set_job_status(delivery_id, repository_id, "completed")

    def fail_ingestion_job(self, delivery_id: str, repository_id: str) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE ingestion_jobs SET status=CASE WHEN attempts >= 2 THEN 'dead_letter' ELSE 'failed' END, lease_until=NULL WHERE delivery_id=%s AND repository_id=%s",
                (delivery_id, repository_id),
            )
        self.connection.commit()

    def _set_job_status(self, delivery_id: str, repository_id: str, status: str) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE ingestion_jobs SET status=%s, lease_until=NULL WHERE delivery_id=%s AND repository_id=%s",
                (status, delivery_id, repository_id),
            )
        self.connection.commit()

    def ingestion_job_status(self) -> dict[str, int]:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT status, COUNT(*) FROM ingestion_jobs GROUP BY status")
            rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}

    @staticmethod
    def _repository(repository_id, row):
        from .records import RepositoryRecord
        return RepositoryRecord(repository_id, row[1], row[2], row[3], row[4], row[5], row[6] if len(row) > 6 else "succeeded", row[7] if len(row) > 7 else None)

    @staticmethod
    def _evidence(row):
        from .records import EvidenceRecord
        return EvidenceRecord(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8] if len(row) > 8 else None)

    @staticmethod
    def _memory(row):
        from .records import MemoryRecord
        return MemoryRecord(row[0], row[1], row[2], row[3], row[4], row[5])
