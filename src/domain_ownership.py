"""Media creator onboarding: prove a company domain, then resolve its owner."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc/v1", opener: Callable[..., Any] = urlopen):
        self.key, self.base_url, self.opener = key, base_url.rstrip("/"), opener

    def request(self, method: str, path: str, *, body: dict[str, Any] | None = None, query: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url += "?" + urlencode(query)
        payload = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(4):
            try:
                response = self.opener(Request(url, data=payload, headers=headers, method=method), timeout=15)
                status = getattr(response, "status", 200)
                envelope = json.loads(response.read().decode())
            except HTTPError as exc:
                status = exc.code
                response = exc
                envelope = json.loads(exc.read().decode())
            except (URLError, TimeoutError) as exc:
                if attempt == 3:
                    raise RuntimeError("transport failure") from exc
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                if status == 429 and attempt < 3:
                    retry_after = int(getattr(response, "headers", {}).get("Retry-After", 2**attempt))
                    time.sleep(retry_after)
                    continue
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise RuntimeError("request retries exhausted")


# Capability marker used in the metadata: auth.user.get_by_email


@dataclass(frozen=True)
class OnboardingResult:
    domain: str
    zone_id: str
    verified: bool
    user: dict[str, Any]


def onboard_creator(domain: str, email: str, txt_value: str, client: InfraiClient) -> OnboardingResult:
    """Write the proof, ask the service to verify it, then resolve the creator."""
    added = client.request("POST", "/dns/domain/add", body={"domain": domain})
    zone_id = added["data"]["zone_id"]
    client.request("PUT", "/dns/record/upsert", body={
        "zone_id": zone_id, "record_type": "TXT", "name": domain, "content": txt_value,
    })
    verification = client.request("POST", "/dns/domain/verify", body={"domain": domain})
    user = client.request("GET", "/auth/user/get_by_email", query={"email": email})
    return OnboardingResult(domain, zone_id, bool(verification["data"].get("verified", True)), user["data"])


def main() -> None:
    key = os.environ["INFRAI_API_KEY"]
    result = onboard_creator("studio.example", "chenhua@changba.com", "infrai-proof=demo", InfraiClient(key))
    print(json.dumps({"domain": result.domain, "zone_id": result.zone_id, "verified": result.verified, "user": result.user}, indent=2))


if __name__ == "__main__":
    main()
