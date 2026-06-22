"""AC-P3: NAV estimate drift degradation acceptance.

PRD 1.2 rule (dev-004 fetcher.pipeline.real_poc):
- abs(iopv - nav_official) / nav_official >= 1% must mark source_quality=degraded
  and surface failure_reason "nav_estimate_drift:<signed>".
- A code that stays non-ok for two consecutive minutes is upgraded to stale
  (failure_reason "stale_consecutive_failures:N").

Method: reuse dev-004's parse_realtime_source_payload / run_long_run with offline
injected payloads (no network). Verify the >=1% threshold boundary and the
two-minute stale escalation. Also assert the threshold constant equals 1%.

Pass criteria: <1% drift stays ok; >=1% drift is degraded; two consecutive
degraded minutes escalate to stale; threshold constant == 0.01.
Dependency: dev-004 (fetcher real_poc degradation logic).
Current status: implemented (offline deterministic, no network / no online API).
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from _lib import AC

META = AC.P3
DRIFT_THRESHOLD = 0.01

# PRD 1.2.1: ??????????????????? dev-004 ?????
# ?? IOPV ??????? AC-P3???? skip??????????????
pytestmark = pytest.mark.skip(
    reason="?????????PRD 1.2.1 ????????? dev-004 ???????IOPV?????"
)


def _load_real_poc(project_root: Path):
    fetcher_root = project_root / "lof-fetcher"
    if str(fetcher_root) not in sys.path:
        sys.path.insert(0, str(fetcher_root))
    import fetcher.pipeline.real_poc as real_poc

    return real_poc


def _payload(price, iopv, nav_official, estimate_time="2026-06-18 15:00"):
    return {
        "price": {"price": price, "source": "tencent_quote", "elapsed_ms": 5, "name": "x"},
        "nav": {
            "iopv": iopv,
            "nav": nav_official,
            "source": "fundgz",
            "elapsed_ms": 5,
            "estimate_time": estimate_time,
            "name": "x",
        },
    }


@pytest.mark.ac_p
def test_ac_p3_threshold_constant_is_one_percent(project_root):
    assert META.code == "AC-P3"
    real_poc = _load_real_poc(project_root)
    assert real_poc.NAV_DRIFT_DEGRADED_THRESHOLD == DRIFT_THRESHOLD


@pytest.mark.ac_p
def test_ac_p3_drift_below_threshold_stays_ok(project_root):
    real_poc = _load_real_poc(project_root)
    # 0.1% drift -> ok
    payloads = {"161725": _payload(1.00, 1.001, 1.000)}
    report = real_poc.parse_realtime_source_payload(
        ["161725"], payloads, "2026-06-18T15:00:30+08:00"
    )
    item = report["items"][0]
    assert item["source_quality"] == "ok"
    assert abs(item["nav_drift_pct"]) < DRIFT_THRESHOLD
    assert "nav_estimate_drift" not in (item["failure_reason"] or "")


@pytest.mark.ac_p
@pytest.mark.parametrize("iopv,nav_official", [(1.030, 1.000), (0.970, 1.000), (1.010, 1.000)])
def test_ac_p3_drift_at_or_above_threshold_is_degraded(project_root, iopv, nav_official):
    real_poc = _load_real_poc(project_root)
    payloads = {"161725": _payload(1.05, iopv, nav_official)}
    report = real_poc.parse_realtime_source_payload(
        ["161725"], payloads, "2026-06-18T15:00:30+08:00"
    )
    item = report["items"][0]
    drift = (iopv - nav_official) / nav_official
    assert abs(drift) >= DRIFT_THRESHOLD
    assert item["source_quality"] == "degraded"
    assert "nav_estimate_drift" in (item["failure_reason"] or "")


@pytest.mark.ac_p
def test_ac_p3_two_consecutive_minutes_escalate_to_stale(project_root, tmp_path):
    real_poc = _load_real_poc(project_root)

    def fake_build(ts=None, codes=None, stale_threshold_seconds=real_poc.DEFAULT_STALE_THRESHOLD_SECONDS):
        payloads = {"161725": _payload(1.05, 1.030, 1.000)}
        return real_poc.parse_realtime_source_payload(
            ["161725"], payloads, ts, stale_threshold_seconds=stale_threshold_seconds
        )

    original_build = real_poc.build_poc_report
    real_poc.build_poc_report = fake_build
    try:
        base = datetime.fromisoformat("2026-06-18T15:00:00+08:00")
        counter = {"n": 0}

        def now():
            counter["n"] += 1
            return base + timedelta(seconds=30 * counter["n"])

        snapshot_file = tmp_path / "ac-p3-drift-stale.jsonl"
        summary = real_poc.run_long_run(
            duration_minutes=0,
            interval_seconds=0,
            output_dir=tmp_path,
            snapshot_file=snapshot_file,
            iterations=3,
            sleeper=lambda _s: None,
            now=now,
        )
    finally:
        real_poc.build_poc_report = original_build

    qualities = []
    for line in snapshot_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        import json

        batch = json.loads(line)
        qualities.append(batch["items"][0]["source_quality"])

    assert qualities[0] == "degraded", "first minute should be degraded"
    assert "stale" in qualities[1:], "consecutive drift must escalate to stale"
    assert summary["degraded_total"] >= 1
    assert summary["stale_total"] >= 1
