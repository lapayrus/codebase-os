from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkCase:
    question: str
    expected_paths: frozenset[str]
    must_abstain: bool = False


def score_case(case: BenchmarkCase, answer_paths: set[str], has_claims: bool) -> float:
    if case.must_abstain:
        return 1.0 if not has_claims else 0.0
    if not case.expected_paths:
        return 1.0 if not has_claims else 0.0
    return len(case.expected_paths.intersection(answer_paths)) / len(case.expected_paths)
