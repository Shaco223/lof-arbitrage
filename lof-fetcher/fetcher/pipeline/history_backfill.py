# Real daily history backfill + 30-trading-day percentile (PRD M3.9).
#
# For each LOF: align real close_price (eastmoney/tencent kline) with real
# official_nav (ttjj LSJZ) BY TRADING DATE, compute premium_close, and a rolling
# 30-trading-day percentile. No fallback synthesis is ever written here.
from __future__ import annotations

import io
import json
import os
from pathlib import Path
from typing import Any

from fetcher.sources.history import HistoryClient

PCTILE_WINDOW = 30


def _round6(value: float) -> float:
    return round(value, 6)


def compute_premium_pctile(values: list[float | None], index: int, window: int = PCTILE_WINDOW) -> float | None:
    # Sample = non-null premium_close over the trailing `window` trading days
    # ending at `index` (inclusive). Insufficient sample (< window valid) -> None.
    current = values[index]
    if current is None:
        return None
    start = max(0, index - window + 1)
    sample = [v for v in values[start:index + 1] if v is not None]
    if len(sample) < window:
        return None
    less_or_equal = sum(1 for v in sample if v <= current)
    return _round6(less_or_equal / len(sample))


def build_history_records(code: str, closes: dict[str, float], navs: dict[str, float]) -> list[dict[str, Any]]:
    # Trading dates are driven by close_price availability (kline = trading days).
    dates = sorted(closes.keys())
    premiums: list[float | None] = []
    base_rows: list[dict[str, Any]] = []
    for date in dates:
        close_price = closes.get(date)
        official_nav = navs.get(date)
        premium_close = None
        if close_price is not None and official_nav is not None and official_nav > 0:
            premium_close = _round6(close_price / official_nav - 1)
        premiums.append(premium_close)
        base_rows.append({
            "code": code,
            "date": date,
            "close_price": close_price,
            "official_nav": official_nav,
            "premium_close": premium_close,
        })
    for idx, row in enumerate(base_rows):
        row["premium_pctile_30d"] = compute_premium_pctile(premiums, idx)
    return base_rows


def backfill_code(client: HistoryClient, code: str, limit: int = 60) -> dict[str, Any]:
    close_payload = client.fetch_close_prices(code, limit=limit)
    nav_payload = client.fetch_official_navs(code, page_size=limit)
    records = build_history_records(code, close_payload.get("closes") or {}, nav_payload.get("navs") or {})
    valid_premium = sum(1 for r in records if r["premium_close"] is not None)
    return {
        "code": code,
        "close_source": close_payload.get("source") or "",
        "nav_source": nav_payload.get("source") or "",
        "close_error": close_payload.get("error") or "",
        "nav_error": nav_payload.get("error") or "",
        "trading_days": len(records),
        "valid_premium_days": valid_premium,
        "records": records,
    }


DEFAULT_HISTORY_FILE = "local-history-daily-v2.jsonl"


def _record_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("code")), str(row.get("date")))


def load_history_file(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with io.open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def merge_records(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Merge by (code, date). Never overwrite a CONFIRMED official_nav (non-null)
    # with a null/missing one; otherwise prefer the newest payload (fills T+1 gaps).
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for row in existing:
        merged[_record_key(row)] = dict(row)
    for row in incoming:
        key = _record_key(row)
        prev = merged.get(key)
        if prev is None:
            merged[key] = dict(row)
            continue
        new_row = dict(prev)
        if row.get("close_price") is not None:
            new_row["close_price"] = row["close_price"]
        # Only fill official_nav if newly available; keep confirmed value otherwise.
        if row.get("official_nav") is not None:
            new_row["official_nav"] = row["official_nav"]
        merged[key] = new_row
    return list(merged.values())


def recompute_series(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Recompute premium_close + rolling 30d percentile per code over the full
    # merged trading-day series (sorted by date).
    by_code: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_code.setdefault(str(row.get("code")), []).append(row)
    out: list[dict[str, Any]] = []
    for code, code_rows in by_code.items():
        code_rows.sort(key=lambda r: str(r.get("date")))
        premiums: list[float | None] = []
        for row in code_rows:
            close_price = row.get("close_price")
            official_nav = row.get("official_nav")
            premium_close = None
            if close_price is not None and official_nav is not None and official_nav > 0:
                premium_close = _round6(close_price / official_nav - 1)
            row["premium_close"] = premium_close
            premiums.append(premium_close)
        for idx, row in enumerate(code_rows):
            row["premium_pctile_30d"] = compute_premium_pctile(premiums, idx)
        out.extend(code_rows)
    return out


def save_history_file(path: str | Path, rows: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows, key=lambda r: (str(r.get("code")), str(r.get("date"))))
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in ordered:
            handle.write(json.dumps({
                "code": row.get("code"),
                "date": row.get("date"),
                "close_price": row.get("close_price"),
                "official_nav": row.get("official_nav"),
                "premium_close": row.get("premium_close"),
                "premium_pctile_30d": row.get("premium_pctile_30d"),
            }, ensure_ascii=False) + "\n")


def run_history_backfill(
    codes: list[str],
    history_file: str | Path,
    limit: int = 60,
    client: HistoryClient | None = None,
) -> dict[str, Any]:
    owns_client = client is None
    client = client or HistoryClient()
    per_code: list[dict[str, Any]] = []
    incoming: list[dict[str, Any]] = []
    try:
        for code in codes:
            result = backfill_code(client, code, limit=limit)
            incoming.extend(result.pop("records"))
            per_code.append(result)
    finally:
        if owns_client:
            client.close()

    existing = load_history_file(history_file)
    merged = merge_records(existing, incoming)
    merged = recompute_series(merged)
    save_history_file(history_file, merged)

    by_code_count: dict[str, int] = {}
    sufficient = 0
    for row in merged:
        by_code_count[str(row.get("code"))] = by_code_count.get(str(row.get("code")), 0) + 1
    for code in {str(r.get("code")) for r in merged}:
        rows = [r for r in merged if str(r.get("code")) == code]
        if sum(1 for r in rows if r.get("premium_pctile_30d") is not None) > 0:
            sufficient += 1

    return {
        "history_file": str(history_file),
        "target_count": len(codes),
        "total_records": len(merged),
        "codes_with_pctile": sufficient,
        "per_code": per_code,
    }
