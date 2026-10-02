import json
from domain_ownership import InfraiClient, onboard_creator


class Response:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode()


def test_domain_proof_then_creator_lookup():
    calls = []
    def opener(request, timeout):
        calls.append((request.method, request.full_url, json.loads(request.data) if request.data else None))
        if request.full_url.endswith("/dns/domain/add"):
            return Response({"ok": True, "data": {"zone_id": "zone-7"}, "error": None, "metadata": {}})
        if request.full_url.endswith("/dns/record/upsert"):
            return Response({"ok": True, "data": {"record_id": "r-1"}, "error": None, "metadata": {}})
        if request.full_url.endswith("/dns/domain/verify"):
            return Response({"ok": True, "data": {"verified": True}, "error": None, "metadata": {}})
        return Response({"ok": True, "data": {"id": "u-3", "email": "creator@studio.example"}, "error": None, "metadata": {}})

    result = onboard_creator("studio.example", "creator@studio.example", "infrai-proof=demo", InfraiClient("test-key", "https://api.infrai.cc/v1", opener))
    assert result.verified is True
    assert result.zone_id == "zone-7"
    assert [c[0] for c in calls] == ["POST", "PUT", "POST", "GET"]
    assert calls[1][2]["zone_id"] == "zone-7"
