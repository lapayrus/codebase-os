import json
import pytest
from codebase_os.models_gateway import ModelGateway
from codebase_os.retrieval.context import ContextPacket


class FakeProvider:
    name = "fake"

    def complete(self, question, packet):
        return json.dumps({"claims": [{"text": "supported", "confidence": "high", "evidence_ids": [0]}], "caveats": []})


def test_gateway_parses_structured_claims():
    packet = ContextPacket((), 0, 0, "abc")
    response = ModelGateway(FakeProvider()).answer("question", packet, [])
    assert response.model == "fake"
    assert response.claims[0].evidence_ids == [0]


def test_gateway_rejects_malformed_output():
    class Broken:
        def complete(self, question, packet):
            return "not json"
    with pytest.raises(ValueError, match="structured JSON"):
        ModelGateway(Broken()).answer("question", ContextPacket((), 0, 0, "abc"), [])

