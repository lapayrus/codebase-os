from datetime import datetime, timezone
from pathlib import Path
import hashlib

from .base import RepositorySnapshot, SnapshotFile

TEXT_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb", ".php", ".cs", ".md", ".yml", ".yaml", ".json", ".toml", ".sql", ".sh"}
IGNORED_DIRS = {".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__", ".next", "coverage"}
SECRET_MARKERS = ("-----BEGIN", "aws_secret_access_key", "private_key", "api_key", "password=")


class LocalRepositoryProvider:
    def __init__(self, root: str, max_file_bytes: int = 1_000_000) -> None:
        self.root = Path(root).resolve()
        self.max_file_bytes = max_file_bytes

    def snapshot(self, repository_id: str, branch: str = "main") -> RepositorySnapshot:
        if not self.root.is_dir():
            raise ValueError(f"Repository directory does not exist: {self.root}")
        files: list[SnapshotFile] = []
        skipped: list[str] = []
        diagnostics: list[str] = []
        digest = hashlib.sha1()
        for path in sorted(self.root.rglob("*")):
            relative = path.relative_to(self.root).as_posix()
            if not path.is_file() or any(part in IGNORED_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                skipped.append(relative)
                continue
            size = path.stat().st_size
            if size > self.max_file_bytes:
                skipped.append(relative)
                diagnostics.append(f"Skipped oversized file: {relative}")
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                skipped.append(relative)
                diagnostics.append(f"Skipped unreadable or binary file: {relative}")
                continue
            if any(marker.lower() in content.lower() for marker in SECRET_MARKERS):
                diagnostics.append(f"Potential secret content detected: {relative}")
            digest.update(relative.encode("utf-8"))
            digest.update(content.encode("utf-8"))
            files.append(SnapshotFile(relative, content, size, datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)))
        return RepositorySnapshot("local", repository_id, self.root.name, branch, digest.hexdigest()[:12], tuple(files), tuple(skipped), tuple(diagnostics))
