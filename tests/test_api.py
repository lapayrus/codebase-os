from pathlib import Path
from fastapi.testclient import TestClient
from codebase_os.indexer import index_repository
from codebase_os.main import app, service


def test_query_rejects_repository_outside_access_header(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    service.add_repository(index_repository(str(tmp_path), "secure"))
    response = TestClient(app).post('/api/query', headers={'x-repository-access': 'other'}, json={'repository': 'secure', 'question': 'Where is hello?'})
    assert response.status_code == 403
    service.repositories.pop('secure', None)

