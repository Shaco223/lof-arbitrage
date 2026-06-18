from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fetcher.engine.premium import calculate_premium
from fetcher.sources.realtime_poc import POC_CODES, RealTimePocClient

DEFAULT_SNAPSHOT_PATH = Path(__file__).resolve().parents[3] / "outputs" / "local-minute-snapshots-v2.jsonl"


def build_poc_report(
    payloads: dict[str, dict[str, Any]] | None = None,
    ts: str | None = None,
    codes: list[str] | None = None,
) -> dict[str, Any]:
    target_codes = codes or POC_CODES
    if payloads is None:
        client = RealTimePocClient()
        try:
            payloads = {code: client.fetch_code_payload(code) for code in target_codes}
        finally:
            client.close()
    return parse_realtime_source_payload(target_codes, payloads, ts or datetime.now().astimezone().isoformat(timespec="seconds"))


def parse_realtime_source_payload(codes: list[str], payloads: dict[str, dict[str, Any]], ts: str) -> dict[str, Any]:
    items = []
    elapsed_ms = 0
    ok_count = 0
    degraded_count = 0

    for code in codes:
        payload = payloads.get(code, {})
        price_payload = payload.get("price", {}) or {}
        nav_payload = payload.get("nav", {}) or {}
        elapsed_ms += int(price_payload.get("elapsed_ms") or 0) + int(nav_payload.get("elapsed_ms") or 0)
        price = _number_or_none(price_payload.get("price"))
        iopv = _number_or_none(nav_payload.get("iopv"))
        premium = calculate_premium(price, iopv) if price is not None and iopv is not None and iopv > 0 else None
        failure_reason = _failure_reason(price_payload, nav_payload, price, iopv)
        source_quality = "ok" if premium is not None and not failure_reason else "degraded"
        if source_quality == "ok":
            ok_count += 1
        else:
            degraded_count += 1
        items.append(
            {
                "code": code,
                "name": price_payload.get("name") or nav_payload.get("name") or code,
                "price": price,
                "iopv": iopv,
                "premium": premium,
                "coverage": 1.0 if source_quality == "ok" else 0.0,
                "source_quality": source_quality,
                "failure_reason": failure_reason,
                "sources": {
                    "price": price_payload.get("source") or "",
                    "nav": nav_payload.get("source") or "",
                },
                "elapsed_ms": int(price_payload.get("elapsed_ms") or 0) + int(nav_payload.get("elapsed_ms") or 0),
            }
        )

    target_count = len(codes)
    return {
        "ts": ts,
        "summary": {
            "target_count": target_count,
            "ok_count": ok_count,
            "degraded_count": degraded_count,
            "field_completeness": round(ok_count / target_count, 6) if target_count else 0.0,
            "elapsed_ms": elapsed_ms,
        },
        "items": items,
    }


def write_poc_outputs(report: dict[str, Any], output_dir: str | Path, snapshot_path: str | Path | None = None) -> dict[str, Path]:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / "backend-real-poc-report-v2.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    jsonl_path = Path(snapshot_path) if snapshot_path else DEFAULT_SNAPSHOT_PATH
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "ts": report["ts"],
        "items": [
            {
                "code": item["code"],
                "price": item["price"],
                "iopv": item["iopv"],
                "premium": item["premium"],
                "coverage": item["coverage"],
                "source_quality": item["source_quality"],
            }
            for item in report["items"]
        ],
    }
    with jsonl_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
    return {"report": report_path, "snapshot": jsonl_path}


def _failure_reason(price_payload: dict[str, Any], nav_payload: dict[str, Any], price: float | None, iopv: float | None) -> str:
    reasons = []
    if price_payload.get("error"):
        reasons.append(str(price_payload["error"]))
    if nav_payload.get("error"):
        reasons.append(str(nav_payload["error"]))
    if price is None:
        reasons.append("missing_market_price")
    if iopv is None:
        reasons.append("missing_estimated_nav")
    return ";".join(dict.fromkeys(reasons))


def _number_or_none(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
