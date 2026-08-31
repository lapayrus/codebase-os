from pathlib import Path
from codebase_os.ingestion.jobs import IngestionJobRunner
from codebase_os.providers.local import LocalRepositoryProvider


def test_local_snapshot_skips_binary_and_oversized_files(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"binary")
    (tmp_path / "large.py").write_text("x" * 200, encoding="utf-8")
    snapshot = LocalRepositoryProvider(str(tmp_path), max_file_bytes=100).snapshot("repo-a")
    assert [item.path for item in snapshot.files] == ["main.py"]
    assert "image.png" in snapshot.skipped_paths
    assert any("large.py" in item for item in snapshot.diagnostics)


def test_ingestion_is_idempotent(tmp_path: Path):
    (tmp_path / "main.py").write_text("print('ok')", encoding="utf-8")
    snapshot = LocalRepositoryProvider(str(tmp_path)).snapshot("repo-a")
    runner = IngestionJobRunner()
    assert runner.process(snapshot).indexed is True
    assert runner.process(snapshot).indexed is False
