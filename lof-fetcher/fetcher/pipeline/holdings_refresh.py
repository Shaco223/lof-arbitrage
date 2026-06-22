from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fetcher.sources.csv_assets import LofMeta, load_watchlist
from fetcher.sources.holdings import HoldingsClient, HoldingsResult
from fetcher.sources.stock_quote import StockQuoteClient

DEFAULT_WATCHLIST_PATH = Path(__file__).resolve().parents[3] / "assets" / "lof-watchlist-v2.csv"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[3] / "outputs"
DEFAULT_SAMPLE_DATASET = (
    Path(__file__).resolve().parents[3] / "uniCloud-aliyun" / "tests" / "sample-dataset.json"
)
DEFAULT_HOLDINGS_CACHE = "backend-real-holdings-v2.json"
DEFAULT_HOLDINGS_REPORT = "backend-real-holdings-report-v2.json"


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def build_holdings_payload(
    metas: list[LofMeta],
    *,
    ts: str,
    with_realtime: bool = True,
) -> dict[str, Any]:
    """Fetch quarterly top-10 holdings for each LOF and overlay live stock change pct.

    Degrade gracefully:
      - LOF holdings unavailable -> empty list (front-end hides table, AC-P5).
      - live change pct unavailable -> price_change_pct/contribution_pct = null.
    """
    holdings_client = HoldingsClient()
    results: dict[str, HoldingsResult] = {}
    all_stock_codes: set[str] = set()
    try:
        for meta in metas:
            res = holdings_client.fetch_holdings(meta.code)
            results[meta.code] = res
            for row in res.rows:
                all_stock_codes.add(row.stock_code)
    finally:
        holdings_client.close()

    change_pct_map: dict[str, float | None] = {}
    if with_realtime and all_stock_codes:
        quote_client = StockQuoteClient()
        try:
            change_pct_map = quote_client.fetch_change_pct(sorted(all_stock_codes))
        finally:
            quote_client.close()

    holdings_rows: list[dict[str, Any]] = []
    per_lof: list[dict[str, Any]] = []
    fetched = 0
    missing = 0
    for meta in metas:
        res = results.get(meta.code)
        if res is None or not res.rows:
            missing += 1
            per_lof.append(
                {
                    "code": meta.code,
                    "name": meta.name,
                    "type": meta.type,
                    "report_date": res.report_date if res else None,
                    "holdings_count": 0,
                    "error": res.error if res else "no_result",
                    "elapsed_ms": res.elapsed_ms if res else 0,
                }
            )
            continue
        fetched += 1
        for row in res.rows:
            change_pct = change_pct_map.get(row.stock_code)
            contribution = (
                round6(row.weight * change_pct)
                if change_pct is not None and row.weight is not None
                else None
            )
            holdings_rows.append(
                {
                    "code": meta.code,
                    "report_date": row.report_date,
                    "stock_code": row.stock_code,
                    "stock_name": row.stock_name,
                    "weight": round6(row.weight),
                    "price_change_pct": round6(change_pct),
                    "contribution_pct": contribution,
                }
            )
        per_lof.append(
            {
                "code": meta.code,
                "name": meta.name,
                "type": meta.type,
                "report_date": res.report_date,
                "holdings_count": len(res.rows),
                "error": res.error,
                "elapsed_ms": res.elapsed_ms,
            }
        )

    summary = {
        "ts": ts,
        "target_count": len(metas),
        "fetched_count": fetched,
        "missing_count": missing,
        "stock_universe": len(all_stock_codes),
        "realtime_applied": bool(with_realtime and all_stock_codes),
    }
    return {"summary": summary, "per_lof": per_lof, "holdings": holdings_rows}


def update_sample_dataset_holdings(
    payload: dict[str, Any],
    dataset_path: Path = DEFAULT_SAMPLE_DATASET,
) -> int:
    """Replace lof_holdings in sample-dataset.json with real holdings.

    Only LOFs that have real holdings get overwritten; LOFs with no real data
    keep an empty array so the front-end hides the table (AC-P5).
    """
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    fetched_codes = {row["code"] for row in payload["holdings"]}
    all_codes = {entry["code"] for entry in payload["per_lof"]}
    kept = [
        row
        for row in dataset.get("lof_holdings", [])
        if row.get("code") not in all_codes
    ]
    new_rows = list(payload["holdings"])
    dataset["lof_holdings"] = kept + new_rows
    dataset_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return len(new_rows)


def write_holdings_outputs(
    payload: dict[str, Any],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = output_dir / DEFAULT_HOLDINGS_CACHE
    report_path = output_dir / DEFAULT_HOLDINGS_REPORT
    cache_path.write_text(
        json.dumps({"ts": payload["summary"]["ts"], "holdings": payload["holdings"]}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    report_path.write_text(
        json.dumps({"summary": payload["summary"], "per_lof": payload["per_lof"]}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return {"cache": cache_path, "report": report_path}


def run_holdings_refresh(
    *,
    watchlist_path: Path = DEFAULT_WATCHLIST_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dataset_path: Path = DEFAULT_SAMPLE_DATASET,
    ts: str | None = None,
    with_realtime: bool = True,
    write_dataset: bool = True,
) -> dict[str, Any]:
    metas = load_watchlist(watchlist_path)
    ts = ts or datetime.now().astimezone().isoformat(timespec="seconds")
    payload = build_holdings_payload(metas, ts=ts, with_realtime=with_realtime)
    files = write_holdings_outputs(payload, output_dir)
    written = 0
    if write_dataset:
        written = update_sample_dataset_holdings(payload, dataset_path)
    payload["summary"]["dataset_rows_written"] = written
    payload["summary"]["files"] = {name: str(path) for name, path in files.items()}
    return payload
