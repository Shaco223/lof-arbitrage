from __future__ import annotations

import json
from pathlib import Path

from fetcher.main import main


def test_main_writes_retry_trace_and_quota_outputs(tmp_path):
    main(["ac-evidence", "--output-dir", str(tmp_path)])

    success_events = [json.loads(line) for line in (tmp_path / "backend-ac-c2-retry-success-v2.jsonl").read_text(encoding="utf-8").splitlines()]
    failure_events = [json.loads(line) for line in (tmp_path / "backend-ac-c2-retry-failure-v2.jsonl").read_text(encoding="utf-8").splitlines()]
    quota = json.loads((tmp_path / "backend-ac-s1-quota-estimate-v2.json").read_text(encoding="utf-8"))

    assert [event["status"] for event in success_events] == ["failed", "failed", "success"]
    assert [event["status"] for event in failure_events] == ["failed", "failed", "skipped"]
    assert quota["within_budget"] is True
