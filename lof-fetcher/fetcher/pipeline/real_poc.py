from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from fetcher.engine.premium import calculate_premium
from fetcher.sources.realtime_poc import POC_CODES, RealTimePocClient

DEFAULT_SNAPSHOT_PATH = Path(__file__).resolve().parents[3] / "outputs" / "local-minute-snapshots-v2.jsonl"
DEFAULT_REPORT_NAME = "backend-real-poc-report-v2.json"
DEFAULT_STALE_THRESHOLD_SECONDS = 86400
# PRD 1.2 AC-P3: abs(iopv - nav_official) / nav_official >= 1% -> degraded
NAV_DRIFT_DEGRADED_THRESHOLD = 0.01


def build_poc_report(
    payloads: dict[str, dict[str, Any]] | None = None,
    ts: str | None = None,
    codes: list[str] | None = None,
    stale_threshold_seconds: int = DEFAULT_STALE_THRESHOLD_SECONDS,
) -> dict[str, Any]:
    target_codes = codes or POC_CODES
    if payloads is None:
        client = RealTimePocClient()
        try:
            payloads = {code: client.fetch_code_payload(code) for code in target_codes}
        finally:
            client.close()
    return parse_realtime_source_payload(
        target_codes,
        payloads,
        ts or datetime.now().astimezone().isoformat(timespec="seconds"),
        stale_threshold_seconds=stale_threshold_seconds,
    )


def parse_realtime_source_payload(
    codes: list[str],
    payloads: dict[str, dict[str, Any]],
    ts: str,
    stale_threshold_seconds: int = DEFAULT_STALE_THRESHOLD_SECONDS,
) -> dict[str, Any]:
    items = []
    elapsed_ms = 0
    ok_count = 0
    degraded_count = 0
    stale_count = 0

    snapshot_dt = _parse_iso_ts(ts)

    for code in codes:
        payload = payloads.get(code, {})
        price_payload = payload.get("price", {}) or {}
        nav_payload = payload.get("nav", {}) or {}
        elapsed_ms += int(price_payload.get("elapsed_ms") or 0) + int(nav_payload.get("elapsed_ms") or 0)
        price = _number_or_none(price_payload.get("price"))
        iopv = _number_or_none(nav_payload.get("iopv"))
        nav_official = _number_or_none(nav_payload.get("nav"))
        premium = calculate_premium(price, iopv) if price is not None and iopv is not None and iopv > 0 else None
        failure_reason = _failure_reason(price_payload, nav_payload, price, iopv)

        stale_reason = _detect_stale(snapshot_dt, nav_payload.get("estimate_time"), stale_threshold_seconds)
        if stale_reason:
            failure_reason = ";".join(filter(None, [failure_reason, stale_reason]))

        nav_drift_pct = None
        nav_drift_reason = ""
        if iopv is not None and nav_official is not None and nav_official > 0:
            nav_drift_pct = round((iopv - nav_official) / nav_official, 6)
            if abs(nav_drift_pct) >= NAV_DRIFT_DEGRADED_THRESHOLD:
                nav_drift_reason = f"nav_estimate_drift:{nav_drift_pct:+.4f}"
                failure_reason = ";".join(filter(None, [failure_reason, nav_drift_reason]))

        if stale_reason:
            source_quality = "stale"
            stale_count += 1
        elif nav_drift_reason:
            source_quality = "degraded"
            degraded_count += 1
        elif premium is not None and not failure_reason:
            source_quality = "ok"
            ok_count += 1
        else:
            source_quality = "degraded"
            degraded_count += 1

        items.append(
            {
                "code": code,
                "name": price_payload.get("name") or nav_payload.get("name") or code,
                "price": price,
                "iopv": iopv,
                "nav_official": nav_official,
                "nav_drift_pct": nav_drift_pct,
                "premium": premium,
                "coverage": 1.0 if source_quality == "ok" else 0.0,
                "source_quality": source_quality,
                "failure_reason": failure_reason,
                "sources": {
                    "price": price_payload.get("source") or "",
                    "nav": nav_payload.get("source") or "",
                },
                "estimate_time": nav_payload.get("estimate_time") or "",
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
            "stale_count": stale_count,
            "field_completeness": round(ok_count / target_count, 6) if target_count else 0.0,
            "elapsed_ms": elapsed_ms,
        },
        "items": items,
    }


def write_poc_outputs(
    report: dict[str, Any],
    output_dir: str | Path,
    snapshot_path: str | Path | None = None,
) -> dict[str, Path]:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / DEFAULT_REPORT_NAME
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


def run_long_run(
    duration_minutes: float,
    interval_seconds: float,
    output_dir: str | Path,
    snapshot_file: str | Path,
    iterations: int | None = None,
    ts_start: str | None = None,
    sleeper: Callable[[float], None] | None = None,
    stale_threshold_seconds: int = DEFAULT_STALE_THRESHOLD_SECONDS,
    now: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Run real-poc periodically and append snapshots to JSONL.

    `iterations` is provided primarily for unit tests; production callers should
    rely on `duration_minutes`. When both are supplied, the loop stops once
    either is reached.
    """

    sleeper = sleeper or time.sleep
    now_fn = now or (lambda: datetime.now().astimezone())
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    snapshot_path = Path(snapshot_file)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    started_at = now_fn()
    started_iso = ts_start or started_at.isoformat(timespec="seconds")
    deadline = (
        started_at + timedelta(minutes=duration_minutes)
        if duration_minutes > 0
        else None
    )

    iteration = 0
    last_report: dict[str, Any] | None = None
    ok_total = 0
    degraded_total = 0
    stale_total = 0
    elapsed_total_ms = 0
    failure_streak: dict[str, int] = {}

    while True:
        iteration += 1
        loop_ts = (
            ts_start if iteration == 1 and ts_start
            else now_fn().isoformat(timespec="seconds")
        )
        report = build_poc_report(ts=loop_ts, stale_threshold_seconds=stale_threshold_seconds)
        # PRD M2-B: ????????? stale???? OK ????
        for item in report["items"]:
            code = item["code"]
            quality = item["source_quality"]
            if quality == "ok":
                failure_streak[code] = 0
                continue
            failure_streak[code] = failure_streak.get(code, 0) + 1
            if failure_streak[code] >= 2 and quality != "stale":
                item["source_quality"] = "stale"
                item["failure_reason"] = ";".join(
                    filter(None, [item.get("failure_reason") or "", f"stale_consecutive_failures:{failure_streak[code]}"])
                )
        # Recompute counts after streak upgrade.
        ok_count = sum(1 for it in report["items"] if it["source_quality"] == "ok")
        degraded_count = sum(1 for it in report["items"] if it["source_quality"] == "degraded")
        stale_count = sum(1 for it in report["items"] if it["source_quality"] == "stale")
        target_count = report["summary"]["target_count"]
        report["summary"]["ok_count"] = ok_count
        report["summary"]["degraded_count"] = degraded_count
        report["summary"]["stale_count"] = stale_count
        report["summary"]["field_completeness"] = round(ok_count / target_count, 6) if target_count else 0.0
        files = write_poc_outputs(report, output_root, snapshot_path)
        last_report = report

        ok_total += report["summary"]["ok_count"]
        degraded_total += report["summary"]["degraded_count"]
        stale_total += report["summary"].get("stale_count", 0)
        elapsed_total_ms += report["summary"]["elapsed_ms"]

        reached_iter = iterations is not None and iteration >= iterations
        reached_time = deadline is not None and now_fn() >= deadline
        if reached_iter or reached_time:
            break
        sleeper(max(0.0, interval_seconds))

    ended_at = now_fn()
    summary = {
        "iterations": iteration,
        "started_at": started_iso,
        "ended_at": ended_at.isoformat(timespec="seconds"),
        "duration_seconds": int((ended_at - started_at).total_seconds()),
        "interval_seconds": interval_seconds,
        "snapshot_file": str(snapshot_path),
        "report_file": str(output_root / DEFAULT_REPORT_NAME),
        "ok_total": ok_total,
        "degraded_total": degraded_total,
        "stale_total": stale_total,
        "elapsed_total_ms": elapsed_total_ms,
        "last_summary": last_report["summary"] if last_report else None,
    }
    long_run_path = output_root / "backend-real-poc-long-run-v2.json"
    long_run_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary["long_run_file"] = str(long_run_path)
    return summary


def _detect_stale(snapshot_dt: datetime | None, estimate_time: Any, threshold_seconds: int) -> str:
    if not snapshot_dt or not estimate_time:
        return ""
    estimate_dt = _parse_estimate_time(str(estimate_time), snapshot_dt.tzinfo)
    if estimate_dt is None:
        return ""
    delta = (snapshot_dt - estimate_dt).total_seconds()
    if delta > threshold_seconds:
        return f"stale_estimated_nav:{int(delta)}s"
    return ""


def _parse_iso_ts(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None


def _parse_estimate_time(value: str, tzinfo) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            naive = datetime.strptime(value, fmt)
            return naive.replace(tzinfo=tzinfo) if tzinfo is not None else naive
        except ValueError:
            continue
    return None


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
