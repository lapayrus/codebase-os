from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import fnmatch
import os
import re

from .models import Evidence

TEXT_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb", ".php", ".cs", ".md", ".yml", ".yaml", ".json", ".toml", ".sql", ".sh"}
IGNORED_DIRS = {
    ".git", ".uv-cache", ".phase10-unit-tmp", ".pytest-runs", ".test-tmp", ".pytest-tmp",
    ".release-dist", "node_modules", "dist", "build", ".venv", "venv", "__pycache__", ".next", "coverage",
}


@dataclass
class Symbol:
    name: str
    kind: str
    path: str
    line: int


@dataclass
class RepositoryIndex:
    name: str
    root: str
    commit: str
    files: dict[str, str] = field(default_factory=dict)
    symbols: list[Symbol] = field(default_factory=list)
    imports: dict[str, set[str]] = field(default_factory=dict)

    def evidence_for(self, terms: list[str], top_k: int = 8) -> list[Evidence]:
        scored: list[tuple[float, Evidence]] = []
        for path, text in self.files.items():
            score = sum(text.lower().count(term.lower()) for term in terms if term)
            if score == 0:
                continue
            lines = text.splitlines()
            matching = [i for i, line in enumerate(lines) if any(t.lower() in line.lower() for t in terms)]
            for line_no in matching[:3]:
                start = max(0, line_no - 2)
                end = min(len(lines), line_no + 3)
                scored.append((score, Evidence(repository=self.name, commit=self.commit, path=path,
                    start_line=start + 1, end_line=end, snippet="\n".join(lines[start:end]), relevance=float(score))))
        scored.sort(key=lambda pair: (-pair[0], pair[1].path, pair[1].start_line))
        return [item for _, item in scored[:top_k]]

    def structural_evidence(self, terms: list[str]) -> list[Evidence]:
        hits = [s for s in self.symbols if any(t.lower() in s.name.lower() for t in terms)]
        return [Evidence(repository=self.name, commit=self.commit, path=s.path, start_line=s.line,
            end_line=s.line, snippet=f"{s.kind} {s.name} ({s.path}:{s.line})", kind="structure", relevance=1.0)
            for s in hits[:5]]


def _commit_for(root: Path) -> str:
    digest = hashlib.sha1()
    patterns = _gitignore_patterns(root)
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_file() and not _is_ignored(relative, patterns):
            digest.update(str(path.relative_to(root)).encode("utf-8"))
            digest.update(str(path.stat().st_mtime_ns).encode("utf-8"))
            digest.update(str(path.stat().st_size).encode("utf-8"))
    return digest.hexdigest()[:12]


def index_repository(root: str, name: str | None = None) -> RepositoryIndex:
    base = Path(root).resolve()
    if not base.is_dir():
        raise ValueError(f"Repository directory does not exist: {root}")
    index = RepositoryIndex(name=name or base.name, root=str(base), commit=_commit_for(base))
    patterns = _gitignore_patterns(base)
    for current, directories, filenames in os.walk(base):
        current_path = Path(current)
        directories[:] = [directory for directory in directories
                          if not _is_ignored((current_path / directory).relative_to(base).as_posix(), patterns)]
        for filename in filenames:
            path = current_path / filename
            relative = path.relative_to(base).as_posix()
            if path.suffix.lower() not in TEXT_EXTENSIONS or _is_ignored(relative, patterns):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            index.files[relative] = text
            index.symbols.extend(_symbols(relative, text))
            index.imports[relative] = set(_imports(text))
    return index


def _gitignore_patterns(root: Path) -> list[str]:
    try:
        lines = (root / ".gitignore").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        lines = []
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


def _is_ignored(relative: str, patterns: list[str]) -> bool:
    parts = relative.replace("\\", "/").split("/")
    ignored = any(part in IGNORED_DIRS for part in parts)
    target = relative.replace("\\", "/").strip("/")
    for pattern in patterns:
        negated = pattern.startswith("!")
        pattern = pattern[1:] if negated else pattern
        directory = pattern.endswith("/")
        pattern = pattern.rstrip("/").lstrip("/")
        if "/" in pattern:
            match = fnmatch.fnmatchcase(target, pattern) or (directory and target.startswith(pattern + "/"))
        else:
            match = any(fnmatch.fnmatchcase(part, pattern) for part in parts)
        if match:
            ignored = not negated
    return ignored


def _symbols(path: str, text: str) -> list[Symbol]:
    result = []
    patterns = [(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)", "function"), (r"^\s*class\s+([A-Za-z_]\w*)", "class"),
                (r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_]\w*)", "function"),
                (r"^\s*(?:export\s+)?class\s+([A-Za-z_]\w*)", "class")]
    for line_no, line in enumerate(text.splitlines(), 1):
        for pattern, kind in patterns:
            match = re.search(pattern, line)
            if match:
                result.append(Symbol(match.group(1), kind, path, line_no))
    return result


def _imports(text: str) -> list[str]:
    values = []
    for line in text.splitlines():
        match = re.search(r"^\s*(?:from\s+([^\s]+)\s+import|import\s+([^\s;]+)|require\(['\"]([^'\"]+))", line)
        if match:
            values.append(next(group for group in match.groups() if group))
    return values
