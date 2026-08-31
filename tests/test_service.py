from pathlib import Path
from codebase_os.indexer import index_repository
from codebase_os.service import CodebaseService


def test_index_and_query(tmp_path: Path):
    (tmp_path / "auth.py").write_text("class AuthService:\n    def create_session(self, user):\n        return save_session(user)\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("Authentication creates a session for a user.", encoding="utf-8")
    service = CodebaseService(); repo = index_repository(str(tmp_path), "demo"); service.add_repository(repo)
    result = service.query("Where does authentication create a session?", "demo")
    assert result.evidence and result.commit == repo.commit and all(c.evidence_ids for c in result.claims)


def test_unknown_question_abstains(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    service = CodebaseService(); service.add_repository(index_repository(str(tmp_path), "demo"))
    result = service.query("Where is the payment reconciliation pipeline?", "demo")
    assert result.claims == [] and "could not find" in result.answer.lower()


def test_memory_is_retrievable(tmp_path: Path):
    (tmp_path / "main.py").write_text("def deploy():\n    pass\n", encoding="utf-8")
    service = CodebaseService(); service.add_repository(index_repository(str(tmp_path), "demo"))
    service.add_memory("demo", "Deployments require the staging approval gate.", "convention")
    result = service.query("What is the staging approval gate?", "demo")
    assert any(e.kind == "memory" for e in result.evidence)

