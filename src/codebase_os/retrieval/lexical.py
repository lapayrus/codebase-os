from ..models import Evidence


def search(files: dict[str, str], terms: list[str], repository: str, commit: str, limit: int = 8) -> list[Evidence]:
    results = []
    for path, content in files.items():
        score = sum(content.lower().count(term.lower()) for term in terms)
        if not score:
            continue
        lines = content.splitlines()
        for index, line in enumerate(lines):
            if any(term.lower() in line.lower() for term in terms):
                start = max(index - 2, 0)
                end = min(index + 3, len(lines))
                results.append(Evidence(repository=repository, commit=commit, path=path, start_line=start + 1,
                    end_line=end, snippet="\n".join(lines[start:end]), relevance=float(score)))
                break
    return sorted(results, key=lambda item: (-item.relevance, item.path))[:limit]

