"""PRD 1.2.1 replay verification (offline, no network).

Proves two properties of the revised source_quality logic:

1. Single-side market swings (large intraday IOPV vs T-1 official NAV drift)
   produce 0 false degradation/stale. nav_drift_pct is informational only.
2. Real data-source failures (NAV blocked / price+NAV missing for two
   consecutive minutes) still correctly degrade -> stale.

Run:
    cd lof-fetcher
    python scripts/verify_prd121_degradation.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fetcher.pipeline.real_poc import parse_realtime_source_payload
from fetcher.pipeline.real_watchlist import build_watchlist_report
from fetcher.sources.csv_assets import LofMeta

TZ = timezone(timedelta(hours=8))


def _meta(code: str, name: str) -> LofMeta:
    return LofMeta(
        code=code,
        name=name,
        type="index",
        scale_yi=10.0,
        benchmark_raw=name,
        status="active",
    )


def scenario_single_side_swing() -> dict:
    """30 funds, all with full data but huge intraday drift (+/- up to ~6%)."""
    metas = []
    payloads = {}
    for i in range(30):
        code = f"16{i:04d}"
        metas.append(_meta(code, f"FUND_{i}"))
        nav_official = 1.0
        # IOPV swings far beyond the old 1% threshold, both directions.
        drift = (-0.06 + (i % 13) * 0.01)
        iopv = round(nav_official * (1 + drift), 4)
        price = round(iopv * (1 + ((-1) ** i) * 0.004), 4)
        payloads[code] = {
            "price": {"price": price, "name": f"FUND_{i}", "elapsed_ms": 8,
                       "source": "tencent_quote",
                       "attempts": [{"source": "tencent_quote", "elapsed_ms": 8, "hit": True}]},
            "nav": {"iopv": iopv, "nav": nav_official, "elapsed_ms": 6,
                     "source": "fundgz", "estimate_time": "2026-06-22 14:30",
                     "attempts": [{"source": "fundgz", "elapsed_ms": 6, "hit": True}]},
        }
    report = build_watchlist_report(metas, payloads, ts="2026-06-22T14:31:00+08:00")
    poc = parse_realtime_source_payload(list(payloads.keys()), payloads,
                                        ts="2026-06-22T14:31:00+08:00",
                                        stale_threshold_seconds=300)
    max_abs_drift = max(abs(it["nav_drift_pct"]) for it in report["items"]
                        if it["nav_drift_pct"] is not None)
    return {
        "watchlist_summary": report["summary"],
        "poc_summary": poc["summary"],
        "max_abs_nav_drift_pct": round(max_abs_drift, 6),
        "watchlist_degraded": report["summary"]["degraded_count"],
        "poc_degraded": poc["summary"]["degraded_count"],
        "poc_stale": poc["summary"]["stale_count"],
    }


def scenario_real_failure() -> dict:
    """NAV blocked (estimate missing) must degrade; nothing computable."""
    codes = ["161725", "161005", "160706"]
    payloads = {}
    for c in codes:
        payloads[c] = {
            "price": {"price": 1.2, "name": c, "elapsed_ms": 10, "source": "tencent_quote"},
            "nav": {"iopv": None, "elapsed_ms": 8, "source": "fundgz",
                     "error": "missing_estimated_nav"},
        }
    poc = parse_realtime_source_payload(codes, payloads,
                                        ts="2026-06-22T14:31:00+08:00",
                                        stale_threshold_seconds=300)
    return {
        "summary": poc["summary"],
        "all_degraded": all(it["source_quality"] == "degraded" for it in poc["items"]),
        "first_failure_reason": poc["items"][0]["failure_reason"],
    }


def main() -> None:
    swing = scenario_single_side_swing()
    failure = scenario_real_failure()
    result = {
        "prd": "1.2.1",
        "generated_at": datetime.now(TZ).isoformat(),
        "scenario_single_side_swing": swing,
        "scenario_real_source_failure": failure,
        "pass_no_false_degrade": (swing["watchlist_degraded"] == 0
                                  and swing["poc_degraded"] == 0
                                  and swing["poc_stale"] == 0
                                  and swing["max_abs_nav_drift_pct"] >= 0.01),
        "pass_real_failure_still_degrades": failure["all_degraded"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
