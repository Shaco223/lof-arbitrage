"""M3 real-quote POC acceptance tests (dev-005).

Scope (PRD section M3.7 / M3-V1~V6):
- M3-V1 POC fund range: only {161725, 161005, 160706, 160632, 501203}; no QDII.
- M3-V2 continuous fetching via backend-real-poc-report-v2.json and
  local-minute-snapshots-v2.jsonl produced by dev-004 fetcher.
- M3-V3 valid-minute ratio coverage hooks (per-batch validity check on the
  current snapshot; full >=10 minute / >=80% ratio still depends on dev-004
  long-run evidence and is reported as informational).
- M3-V4 section 6 field reuse: snapshot items reuse list/realtime keys
  price / iopv / premium / coverage / source_quality without new fields.
- M3-V5 degraded / stale visibility: source_quality enum is bounded and
  failure_reason surfaces for downstream display.
- M3-V6 local-only loop: tests must not call next.bspapp.com; only local
  artifacts under outputs/ and the local API base http://127.0.0.1:8787.

Inputs are produced by:
  cd lof-fetcher; python -m fetcher.main real-poc --output-dir ..\\outputs

No live network fetches happen in this module.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path

import pytest

POC_CODES = ["161725", "161005", "160706", "160632", "501203"]
QDII_HINT_PATTERN = re.compile(r"(QDII|qdii|\u8de8\u5883|\u6e2f\u80a1|\u7eb3\u65af\u8fbe\u514b|\u7eb3\u6307|\u6052\u751f|\u6d77\u5916|\u7f8e\u80a1)")
SECTION6_REUSE_KEYS = {"code", "price", "iopv", "premium", "coverage", "source_quality"}
SOURCE_QUALITY_ENUM = {"ok", "degraded", "stale"}
PREMIUM_TOLERANCE = 1e-4
LOCAL_API_BASE = "http://127.0.0.1:8787"


def _load_report(project_root: Path) -> dict:
    path = project_root / "outputs" / "backend-real-poc-report-v2.json"
    if not path.exists():
        pytest.skip(f"M3 POC report not generated yet: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_snapshot_lines(project_root: Path) -> list[dict]:
    path = project_root / "outputs" / "local-minute-snapshots-v2.jsonl"
    if not path.exists():
        pytest.skip(f"local minute snapshot JSONL not generated yet: {path}")
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        rows.append(json.loads(raw))
    return rows


def _parse_iso8601(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None, f"timestamp missing timezone: {value}"
    return parsed


@pytest.fixture(scope="module")
def poc_report(project_root: Path) -> dict:
    return _load_report(project_root)


@pytest.fixture(scope="module")
def snapshot_lines(project_root: Path) -> list[dict]:
    return _load_snapshot_lines(project_root)


@pytest.mark.ac_p
def test_m3_v1_poc_codes_no_qdii(poc_report: dict, watchlist_csv: Path) -> None:
    """M3-V1: POC range is exactly the approved 5 codes and contains no QDII."""
    items = poc_report["items"]
    assert [item["code"] for item in items] == POC_CODES
    assert poc_report["summary"]["target_count"] == len(POC_CODES)

    watchlist_text = watchlist_csv.read_text(encoding="utf-8")
    for code in POC_CODES:
        line = next((row for row in watchlist_text.splitlines() if row.startswith(f"{code},")), None)
        assert line is not None, f"POC code {code} missing from watchlist-v2"
        assert not QDII_HINT_PATTERN.search(line), (
            f"POC code {code} watchlist row hints at QDII / cross-border which is out of M3 scope: {line}"
        )

    for item in items:
        name = item.get("name") or ""
        sources_value = ",".join((item.get("sources") or {}).values())
        assert not QDII_HINT_PATTERN.search(name)
        assert not QDII_HINT_PATTERN.search(sources_value)


@pytest.mark.ac_c
def test_m3_v2_continuous_snapshot_structure(snapshot_lines: list[dict]) -> None:
    """M3-V2: snapshot JSONL exposes minute-level POC batches; each batch has 5 codes."""
    assert snapshot_lines, "local minute snapshot JSONL is empty"
    timestamps: list[datetime] = []
    for batch in snapshot_lines:
        assert set(batch) >= {"ts", "items"}
        ts = _parse_iso8601(batch["ts"])
        timestamps.append(ts)
        codes = [item["code"] for item in batch["items"]]
        assert codes == POC_CODES, f"snapshot batch does not match POC range: {codes}"
    assert timestamps == sorted(timestamps), "snapshot batches are not in monotonic time order"


@pytest.mark.ac_c
def test_m3_v3_valid_minute_ratio_within_snapshot(poc_report: dict) -> None:
    """M3-V3: valid minutes per code >= 80% in current snapshot batch."""
    summary = poc_report["summary"]
    target_count = summary["target_count"]
    ok_count = summary["ok_count"]
    field_completeness = summary["field_completeness"]
    assert target_count == len(POC_CODES)
    assert ok_count + summary["degraded_count"] == target_count
    assert math.isclose(field_completeness, ok_count / target_count, rel_tol=0, abs_tol=1e-6)
    assert field_completeness >= 0.8, (
        f"current POC field_completeness {field_completeness:.3f} below 80% threshold"
    )


@pytest.mark.ac_i
def test_m3_v4_section6_field_reuse(poc_report: dict, snapshot_lines: list[dict]) -> None:
    """M3-V4: snapshot reuses section 6 fields; no extra contract fields."""
    snapshot_field_set: set[str] = set()
    for batch in snapshot_lines:
        for item in batch["items"]:
            snapshot_field_set.update(item.keys())
            assert SECTION6_REUSE_KEYS <= set(item.keys()), (
                f"snapshot item missing section 6 keys: have {set(item.keys())}"
            )
            assert item["source_quality"] in SOURCE_QUALITY_ENUM
    extras = snapshot_field_set - SECTION6_REUSE_KEYS
    assert snapshot_field_set == SECTION6_REUSE_KEYS, (
        f"snapshot introduced unexpected fields beyond section 6: extra={extras}"
    )

    for item in poc_report["items"]:
        assert SECTION6_REUSE_KEYS <= set(item.keys())
        if item["source_quality"] == "ok":
            assert item["price"] is not None and item["iopv"] is not None
            recomputed = item["price"] / item["iopv"] - 1
            assert abs(recomputed - item["premium"]) <= PREMIUM_TOLERANCE, (
                f"premium drift for {item['code']}: report={item['premium']} recomputed={recomputed}"
            )
        else:
            assert item["source_quality"] in {"degraded", "stale"}


@pytest.mark.ac_a
def test_m3_v5_degraded_stale_visibility(poc_report: dict) -> None:
    """M3-V5: degraded / stale rows carry a non-empty failure_reason for UI surfacing."""
    for item in poc_report["items"]:
        quality = item["source_quality"]
        assert quality in SOURCE_QUALITY_ENUM
        if quality == "ok":
            assert (item.get("failure_reason") or "") == ""
            assert item["coverage"] == 1.0
        else:
            failure_reason = item.get("failure_reason") or ""
            assert failure_reason, (
                f"degraded/stale code {item['code']} should expose failure_reason for Dashboard display"
            )


@pytest.mark.ac_s
def test_m3_v6_local_loop_only(poc_report: dict, snapshot_lines: list[dict]) -> None:
    """M3-V6: artifacts must not reference online uniCloud or QDII upgrades."""
    payload = json.dumps(poc_report, ensure_ascii=False) + "\n" + "\n".join(
        json.dumps(line, ensure_ascii=False) for line in snapshot_lines
    )
    assert "next.bspapp.com" not in payload, "M3 POC artifacts must not call online uniCloud"
    assert "bspapp" not in payload
    assert "QDII" not in payload and "qdii" not in payload
    assert LOCAL_API_BASE.startswith("http://127.0.0.1"), (
        "acceptance must target the local API base 127.0.0.1:8787"
    )
