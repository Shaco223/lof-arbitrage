"""Daily refresh of subscribe/redeem status + subscribe-limit into lof_meta.

PRD 1.3: subscribe_status / redeem_status / subscribe_limit_amount /
subscribe_limit_period are DAILY-class fields (change rarely). They live on
lof_meta (like fund_scale), NOT in the minute snapshot. The daemon calls this
once per trading day (or on the close transition); local-api / cloud functions
read them straight from lof_meta and pass them through.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fetcher.pipeline.real_watchlist import DEFAULT_SAMPLE_DATASET, DEFAULT_WATCHLIST_PATH
from fetcher.sources.csv_assets import load_watchlist
from fetcher.sources.subscribe_status import fetch_subscribe_status_map

SUBSCRIBE_META_KEYS = (
    "subscribe_status",
    "redeem_status",
    "subscribe_limit_amount",
    "subscribe_limit_period",
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


def update_sample_dataset_subscribe_status(
    status_map: dict[str, dict[str, Any]],
    dataset_path: Path = DEFAULT_SAMPLE_DATASET,
) -> int:
    """Write the 4 daily subscribe/redeem/limit fields into sample-dataset.lof_meta.

    Only codes present in both the status map and lof_meta get updated. Missing /
    failed codes keep their previous value (status falls back to 'unknown' if the
    source returned unknown). §6 field names are unchanged (no CCR).
    """
    if not dataset_path.exists():
        return 0
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    ensure_dataset_metas(dataset)
    updated = 0
    for meta in dataset.get("lof_meta", []):
        info = status_map.get(meta.get("code"))
        if not info:
            continue
        meta["subscribe_status"] = info.get("subscribe_status", "unknown")
        meta["redeem_status"] = info.get("redeem_status", "unknown")
        meta["subscribe_limit_amount"] = info.get("subscribe_limit_amount")
        meta["subscribe_limit_period"] = info.get("subscribe_limit_period")
        updated += 1
    dataset_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return updated


def run_subscribe_status_refresh(
    *,
    watchlist_path: Path | None = None,
    dataset_path: Path = DEFAULT_SAMPLE_DATASET,
    write_dataset: bool = True,
    codes: list[str] | None = None,
) -> dict[str, Any]:
    """Fetch + (optionally) persist the daily subscribe/redeem/limit fields.

    Returns a summary: per-code map, source coverage, and how many metas updated.
    """
    if codes is None:
        metas = load_watchlist(watchlist_path or DEFAULT_WATCHLIST_PATH)
        codes = [m.code for m in metas]
    status_map = fetch_subscribe_status_map(codes)

    by_source: dict[str, int] = {}
    limited_with_amount = 0
    for info in status_map.values():
        by_source[info.get("source", "none")] = by_source.get(info.get("source", "none"), 0) + 1
        if info.get("subscribe_status") == "limited" and info.get("subscribe_limit_amount") is not None:
            limited_with_amount += 1

    updated = 0
    if write_dataset:
        updated = update_sample_dataset_subscribe_status(status_map, dataset_path)

    return {
        "codes": len(codes),
        "updated": updated,
        "by_source": by_source,
        "limited_with_amount": limited_with_amount,
        "status_map": status_map,
    }
