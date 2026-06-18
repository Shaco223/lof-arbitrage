from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import httpx

SourceQuality = Literal["ok", "degraded", "stale"]


@dataclass(frozen=True)
class IngestItem:
    code: str
    price: float
    iopv: float
    premium: float
    coverage: float
    source_quality: SourceQuality = "ok"


def build_payload(ts: str, items: list[IngestItem]) -> dict:
    return {"ts": ts, "items": [asdict(item) for item in items]}


class UniCloudUploader:
    def __init__(self, ingest_url: str, token: str, timeout: float = 10.0) -> None:
        self.ingest_url = ingest_url
        self.token = token
        self.timeout = timeout

    def upload(self, ts: str, items: list[IngestItem]) -> dict:
        if not self.ingest_url:
            raise ValueError("ingest_url is required")
        response = httpx.post(
            self.ingest_url,
            json=build_payload(ts, items),
            headers={"X-Ingest-Token": self.token},
            timeout=self.timeout,
            trust_env=False,
        )
        response.raise_for_status()
        return response.json()
