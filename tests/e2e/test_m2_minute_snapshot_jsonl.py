"""M2 minute snapshot JSONL acceptance tests.

Scope:
- Local JSONL generation via ``uniCloud-aliyun/local-minute-snapshots.js``.
- One JSONL line is one minute batch containing 30 fund items.
- 30 unique LOF codes from watchlist-v2 are present in each minute batch.
- Timestamp is valid ISO-8601 with timezone.
- No online uniCloud read/write is used.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

import pytest


SNAPSHOT_TS = "2026-06-18T10:31:00+08:00"
REQUIRED_ITEM_KEYS = {
    "code",
    "price",
    "iopv",
    "premium",
    "coverage",
    "source_quality",
}


def parse_iso8601_with_timezone(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    return parsed


@pytest.mark.ac_c
def test_m2_minute_snapshot_jsonl_generation(project_root: Path, tmp_path: Path) -> None:
    """Validate local minute snapshot JSONL generation and 30-fund completeness."""
    output_path = tmp_path / "local-minute-snapshots-v2.jsonl"
    script_path = project_root / "uniCloud-aliyun" / "local-minute-snapshots.js"

    result = subprocess.run(
        [
            "node",
            str(script_path),
            "--output",
            str(output_path),
            "--ts",
            SNAPSHOT_TS,
        ],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(result.stdout)

    assert cli_payload["outputPath"] == str(output_path)
    assert cli_payload["ts"] == SNAPSHOT_TS
    assert cli_payload["count"] == 30
    assert output_path.exists()

    lines = [line for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1

    snapshot = json.loads(lines[0])
    assert set(snapshot) == {"ts", "items"}
    assert snapshot["ts"] == SNAPSHOT_TS
    parse_iso8601_with_timezone(snapshot["ts"])

    items = snapshot["items"]
    assert len(items) == 30
    assert len({item["code"] for item in items}) == 30
    for item in items:
        assert REQUIRED_ITEM_KEYS <= set(item)
        assert isinstance(item["code"], str)
        assert isinstance(item["price"], int | float)
        assert isinstance(item["iopv"], int | float)
        assert isinstance(item["premium"], int | float)
        assert isinstance(item["coverage"], int | float)
        assert item["source_quality"] in {"ok", "degraded", "stale"}


@pytest.mark.ac_c
def test_m2_minute_snapshot_jsonl_append_persists_history(project_root: Path, tmp_path: Path) -> None:
    """Validate local-first history persistence by appending multiple minute batches."""
    output_path = tmp_path / "local-minute-snapshots-v2.jsonl"
    script_path = project_root / "uniCloud-aliyun" / "local-minute-snapshots.js"

    for ts in ["2026-06-18T10:31:00+08:00", "2026-06-18T10:32:00+08:00"]:
        subprocess.run(
            ["node", str(script_path), "--output", str(output_path), "--ts", ts],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )

    snapshots = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [snapshot["ts"] for snapshot in snapshots] == [
        "2026-06-18T10:31:00+08:00",
        "2026-06-18T10:32:00+08:00",
    ]
    assert all(len(snapshot["items"]) == 30 for snapshot in snapshots)
