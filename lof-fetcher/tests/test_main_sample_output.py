from __future__ import annotations

import json
from pathlib import Path

from fetcher.main import main


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_main_writes_sample_outputs(tmp_path):
    main([
        "sample-output",
        "--output-dir",
        str(tmp_path),
        "--ts",
        "2026-06-18T10:31:00+08:00",
    ])

    list_payload = json.loads((tmp_path / "backend-sample-api-lof-list-v2.json").read_text(encoding="utf-8"))
    detail_payload = json.loads((tmp_path / "backend-sample-api-lof-detail-v2.json").read_text(encoding="utf-8"))
    history_payload = json.loads((tmp_path / "backend-sample-api-lof-history-v2.json").read_text(encoding="utf-8"))
    ingest_payload = json.loads((tmp_path / "backend-sample-ingest-realtime-v2.json").read_text(encoding="utf-8"))

    assert len(list_payload["data"]["items"]) == 30
    assert "coverage_breakdown" in detail_payload["data"]
    assert len(history_payload["data"]["items"]) == 30
    assert len(ingest_payload["items"]) == 30
