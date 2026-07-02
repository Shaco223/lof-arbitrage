"""Daily refresh of on-exchange shares + confirm days into lof_meta (PRD 1.4).

shares_onexchange / shares_incr_daily / purchase_confirm_day / redeem_confirm_day
are DAILY-class fields (jisilu shares update once per trading day; jjfl confirm
days are a near-static rule). They live on lof_meta (like fund_scale / the PRD
1.3 subscribe fields), NOT in the minute snapshot. The daemon calls this once
per calendar day; local-api / cloud functions read them from lof_meta and pass
them through.

Cookie red line (PRD 1.4 R9): the jisilu Cookie is read only from JISILU_COOKIE
and never persisted. Without it, guests only see the first 20 rows so most
shares come back null -- that is acceptable (AC-P8): the pipeline must not crash.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fetcher.pipeline.real_watchlist import DEFAULT_SAMPLE_DATASET, DEFAULT_WATCHLIST_PATH
from fetcher.sources.csv_assets import load_watchlist
from fetcher.sources.shares_confirm import fetch_shares_confirm_map, get_jisilu_cookie

SHARES_CONFIRM_META_KEYS = (
    "shares_onexchange",
    "shares_incr_daily",
    "purchase_confirm_day",
    "redeem_confirm_day",
)


def ensure_dataset_metas(dataset: dict[str, Any], watchlist_path: Path = DEFAULT_WATCHLIST_PATH) -> None:
    existing = {str(row.get("code")) for row in dataset.get("lof_meta", [])}
    dataset.setdefault("lof_meta", [])
    for meta in load_watchlist(watchlist_path):
        if meta.code in existing:
            continue
        dataset["lof_meta"].append({
            "code": meta.code,
            "name": meta.name,
            "type": meta.type,
            "scale_yi": meta.scale_yi,
            "status": meta.status,
            "coverage_top10": None,
            "coverage_breakdown": {"top10_weight": 0, "benchmark_assigned_weight": 0, "cash_weight": 0},
            "benchmark_raw": meta.benchmark_raw,
            "benchmark_components": [],
            "subscribe_status": "unknown",
            "redeem_status": "unknown",
            "subscribe_limit_amount": None,
            "subscribe_limit_period": None,
            "shares_onexchange": None,
            "shares_incr_daily": None,
            "purchase_confirm_day": None,
            "redeem_confirm_day": None,
        })
        existing.add(meta.code)


def update_sample_dataset_shares_confirm(
    shares_map: dict[str, dict[str, Any]],
    dataset_path: Path = DEFAULT_SAMPLE_DATASET,
) -> int:
    """Write the 4 daily PRD 1.4 fields into sample-dataset.lof_meta.

    Only codes present in both the shares map and lof_meta are updated. Missing /
    failed shares stay null (no source -> null, never synthesized). §6 field
    names are unchanged (PRD 1.4 already authorized; no extra CCR).
    """
    if not dataset_path.exists():
        return 0
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    ensure_dataset_metas(dataset)
    updated = 0
    for meta in dataset.get("lof_meta", []):
        info = shares_map.get(meta.get("code"))
        if not info:
            continue
        meta["shares_onexchange"] = info.get("shares_onexchange")
        meta["shares_incr_daily"] = info.get("shares_incr_daily")
        meta["purchase_confirm_day"] = info.get("purchase_confirm_day")
        meta["redeem_confirm_day"] = info.get("redeem_confirm_day")
        updated += 1
    dataset_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return updated


def run_shares_confirm_refresh(
    *,
    watchlist_path: Path | None = None,
    dataset_path: Path = DEFAULT_SAMPLE_DATASET,
    write_dataset: bool = True,
    codes: list[str] | None = None,
) -> dict[str, Any]:
    """Fetch + (optionally) persist the daily shares + confirm-day fields.

    Returns a summary: per-code map, jisilu coverage, jjfl confirm coverage, the
    cookie presence flag, and how many lof_meta rows were updated.
    """
    if codes is None:
        metas = load_watchlist(watchlist_path or DEFAULT_WATCHLIST_PATH)
        codes = [m.code for m in metas]
    shares_map = fetch_shares_confirm_map(codes)

    shares_hit = sum(1 for v in shares_map.values() if v.get("shares_onexchange") is not None)
    confirm_hit = sum(1 for v in shares_map.values() if v.get("purchase_confirm_day") is not None)

    updated = 0
    if write_dataset:
        updated = update_sample_dataset_shares_confirm(shares_map, dataset_path)

    return {
        "codes": len(codes),
        "updated": updated,
        "shares_coverage": shares_hit,
        "confirm_coverage": confirm_hit,
        "cookie_present": get_jisilu_cookie() is not None,
        "shares_map": shares_map,
    }
