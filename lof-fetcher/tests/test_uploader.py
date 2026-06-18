import json

from fetcher.ingest.uploader import IngestItem, build_payload


def test_build_payload_matches_prd_contract():
    payload = build_payload(
        ts="2026-06-18T10:31:00+08:00",
        items=[
            IngestItem(
                code="161725",
                price=0.823,
                iopv=0.805,
                premium=0.0224,
                coverage=1.0,
                source_quality="ok",
            )
        ],
    )

    assert payload == {
        "ts": "2026-06-18T10:31:00+08:00",
        "items": [
            {
                "code": "161725",
                "price": 0.823,
                "iopv": 0.805,
                "premium": 0.0224,
                "coverage": 1.0,
                "source_quality": "ok",
            }
        ],
    }
    json.dumps(payload)
