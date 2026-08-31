from codebase_os.indexer import index_repository
from codebase_os.models import Claim, Evidence
from codebase_os.retrieval.context import build_context_packet
from codebase_os.retrieval.validation import validate_claims
from pathlib import Path


def test_context_packet_is_bounded(tmp_path: Path):
    (tmp_path / "main.py").write_text("def target():\n    return 'target'\n", encoding="utf-8")
    index = index_repository(str(tmp_path), "demo")
    evidence = index.evidence_for(["target"], top_k=8) * 5
    packet = build_context_packet(evidence, index.commit, limit=2, token_budget=20)
    assert len(packet.evidence) <= 2
    assert packet.token_estimate <= 20


def test_invalid_claims_are_removed():
    evidence = [Evidence(repository="demo", commit="abc", path="main.py", start_line=1, end_line=1, snippet="x")]
    claims = [Claim(text="supported", confidence="high", evidence_ids=[0]), Claim(text="unsupported", confidence="high", evidence_ids=[8])]
    assert [item.text for item in validate_claims(claims, evidence)] == ["supported"]

