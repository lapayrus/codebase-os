from codebase_os.indexer import RepositoryIndex
from codebase_os.models_gateway import ModelGateway
from codebase_os.service import CodebaseService
from codebase_os.audit import AuditLog


class FakeProvider:
    name = "fake"

    def complete(self, question, packet):
        return '{"claims": [{"text": "supported", "confidence": "high", "evidence_ids": [0]}, {"text": "unsupported", "confidence": "low", "evidence_ids": [99]}], "caveats": ["model caveat"]}'


def test_model_claims_are_citation_validated_before_answer_delivery():
    service = CodebaseService(ModelGateway(FakeProvider()))
    service.add_repository(RepositoryIndex("demo", "", "commit", {"main.py": "def answer():\n    return 1\n"}))
    answer = service.query("Where is answer?", "demo")
    assert [claim.text for claim in answer.claims] == ["supported"]
    assert "model caveat" in answer.caveats
    assert answer.answer == "supported"


def test_invalid_model_output_falls_back_to_retrieval_evidence():
    class InvalidProvider:
        def complete(self, question, packet):
            return "not-json"

    service = CodebaseService(ModelGateway(InvalidProvider()))
    service.add_repository(RepositoryIndex("demo", "", "commit", {"main.py": "def answer():\n    return 1\n"}))
    answer = service.query("Where is answer?", "demo")
    assert answer.model == "none"
    assert "invalid" in " ".join(answer.caveats)
    assert answer.claims


def test_audit_metadata_can_record_model_without_credentials():
    event = AuditLog().record("tenant", "user", "query", "demo", "request", {"model": "groq"})
    assert event.metadata == {"model": "groq"}
