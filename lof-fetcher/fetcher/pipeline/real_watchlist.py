from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from fetcher.engine.premium import calculate_premium
from fetcher.sources.csv_assets import LofMeta, load_watchlist
from fetcher.sources.realtime_poc import RealTimePocClient

DEFAULT_WATCHLIST_PATH = Path(__file__).resolve().parents[3] / "assets" / "lof-watchlist-v2.csv"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[3] / "outputs"
DEFAULT_SNAPSHOT_NAME = "local-minute-snapshots-watchlist-v2.jsonl"
DEFAULT_REPORT_NAME = "backend-real-watchlist-report-v2.json"
DEFAULT_LONG_RUN_NAME = "backend-real-watchlist-long-run-v2.json"
DEFAULT_STABILITY_NAME = "backend-real-watchlist-stability-v2.md"
DEFAULT_STABILITY_JSON = "backend-real-watchlist-stability-v2.json"
DEFAULT_SAMPLE_DATASET = (
    Path(__file__).resolve().parents[3] / "uniCloud-aliyun" / "tests" / "sample-dataset.json"
)
# Fields refreshed back into sample-dataset.lof_realtime so the local API computes
# premium_nav with a NAV in the same time-frame as the live price (BUG fix:
# previously nav_official stayed at the 6/18 static placeholder).
REALTIME_REFRESH_KEYS = ("price", "price_change_pct", "volume_amount", "iopv", "premium", "coverage", "source_quality", "nav_official", "nav_official_date")
# Live market fields that MUST reflect the real source on every refresh: when the
# source has no value we write explicit null (no stale placeholder), so the
# front-end can hide them per AC-P5 instead of showing a frozen sample value.
REALTIME_OVERWRITE_NULL_KEYS = ("price_change_pct", "volume_amount")
# Snapshot JSONL must carry nav_official/nav_official_date alongside price so the
# local API computes premium_nav = (price - nav_official)/nav_official in the SAME
# time-frame even on the pure-JSONL read path (daemon not running). Without these
# the front-end divided a live price by the stale 6/17 sample nav -> +156% errors.
# price_change_pct / volume_amount are live market fields in REALTIME_REFRESH_KEYS
# (daemon writeback). They MUST also travel in the snapshot JSONL so the pure-JSONL
# read path (daemon stopped) reflects the real source instead of stale sample
# placeholders. No-source values are written as explicit null (AC-P5), same as
# REALTIME_OVERWRITE_NULL_KEYS, so the front-end hides them rather than showing
# a frozen value.
SECTION6_SNAPSHOT_KEYS = ("code", "price", "price_change_pct", "volume_amount",
                          "iopv", "premium", "coverage", "source_quality",
                          "nav_official", "nav_official_date")
# DEPRECATED (PRD 1.2.1): intraday IOPV-vs-(T-1) NAV drift no longer triggers
# source_quality degradation. Kept only as a reference constant for callers/
# tests that still import it; NOT used in degradation logic anymore.
NAV_DRIFT_DEGRADED_THRESHOLD = 0.01


def load_default_watchlist() -> list[LofMeta]:
    return load_watchlist(DEFAULT_WATCHLIST_PATH)


def fetch_watchlist_payloads(metas: list[LofMeta]) -> dict[str, dict[str, Any]]:
    client = RealTimePocClient()
    payloads: dict[str, dict[str, Any]] = {}
    try:
        for meta in metas:
            payloads[meta.code] = {
                "price": client.fetch_market_price_detailed(meta.code),
                "nav": client.fetch_estimated_nav_detailed(meta.code),
            }
    finally:
        client.close()
    return payloads


def build_watchlist_report(
    metas: list[LofMeta],
    payloads: dict[str, dict[str, Any]],
    ts: str,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    target_count = len(metas)
    ok_count = 0
    degraded_count = 0
    elapsed_total_ms = 0

    for meta in metas:
        payload = payloads.get(meta.code, {})
        price_payload = payload.get("price", {}) or {}
        nav_payload = payload.get("nav", {}) or {}
        price_attempts = list(price_payload.get("attempts") or [])
        nav_attempts = list(nav_payload.get("attempts") or [])
        item_elapsed = int(price_payload.get("elapsed_ms") or 0) + int(nav_payload.get("elapsed_ms") or 0)
        elapsed_total_ms += item_elapsed
        price = _number_or_none(price_payload.get("price"))
        previous_close = _number_or_none(price_payload.get("previous_close"))
        # price_change_pct uses the already-parsed previous_close (no extra request).
        price_change_pct = (
            round(price / previous_close - 1, 6)
            if price is not None and previous_close is not None and previous_close > 0
            else None
        )
        volume_amount = _number_or_none(price_payload.get("volume_amount"))
        iopv = _number_or_none(nav_payload.get("iopv"))
        nav_official = _number_or_none(nav_payload.get("nav"))
        premium = (
            calculate_premium(price, iopv)
            if price is not None and iopv is not None and iopv > 0
            else None
        )
        failure_reason = _failure_reason(price_payload, nav_payload, price, iopv)
        # PRD 1.2.1: nav_drift_pct is an INFORMATIONAL field only (intraday IOPV vs
        # T-1 official NAV). It is normal intraday market movement, NOT a data error,
        # so it MUST NOT trigger source_quality degradation. Estimate accuracy is
        # measured post-close via AC-P3 (premium_error / nav_estimate_error_pct).
        nav_drift_pct = None
        if iopv is not None and nav_official is not None and nav_official > 0:
            nav_drift_pct = round((iopv - nav_official) / nav_official, 6)
        # Degradation depends ONLY on data availability (premium computable + no
        # source failure). Source failures are surfaced via failure_reason.
        if premium is not None and not failure_reason:
            source_quality = "ok"
            ok_count += 1
        else:
            source_quality = "degraded"
            degraded_count += 1
        primary_price_source = _primary_source_hit(price_attempts) or (price_payload.get("source") or "")
        primary_nav_source = _primary_source_hit(nav_attempts) or (nav_payload.get("source") or "")
        backup_used = bool(price_attempts) and not (price_attempts[0].get("hit") is True)
        items.append(
            {
                "code": meta.code,
                "name": price_payload.get("name") or nav_payload.get("name") or meta.name,
                "type": meta.type,
                "status": meta.status,
                "scale_yi": meta.scale_yi,
                "price": price,
                "price_change_pct": price_change_pct,
                "volume_amount": volume_amount,
                "iopv": iopv,
                "nav_official": nav_official,
                "nav_official_date": nav_payload.get("nav_date") or "",
                "nav_drift_pct": nav_drift_pct,
                "premium": premium,
                "coverage": 1.0 if source_quality == "ok" else 0.0,
                "source_quality": source_quality,
                "failure_reason": failure_reason,
                "primary_price_source": primary_price_source,
                "primary_nav_source": primary_nav_source,
                "backup_price_used": backup_used,
                "price_attempts": price_attempts,
                "nav_attempts": nav_attempts,
                "elapsed_ms": item_elapsed,
                "estimate_time": nav_payload.get("estimate_time") or "",
            }
        )

    summary = {
        "target_count": target_count,
        "ok_count": ok_count,
        "degraded_count": degraded_count,
        "field_completeness": round(ok_count / target_count, 6) if target_count else 0.0,
        "elapsed_ms": elapsed_total_ms,
    }
    return {"ts": ts, "summary": summary, "items": items}


def write_watchlist_outputs(
    report: dict[str, Any],
    output_dir: str | Path,
    snapshot_path: str | Path | None = None,
) -> dict[str, Path]:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / DEFAULT_REPORT_NAME
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    jsonl_path = Path(snapshot_path) if snapshot_path else output_root / DEFAULT_SNAPSHOT_NAME
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "ts": report["ts"],
        "items": [
            {key: item[key] for key in SECTION6_SNAPSHOT_KEYS}
            for item in report["items"]
        ],
    }
    with jsonl_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
    return {"report": report_path, "snapshot": jsonl_path}


def update_sample_dataset_realtime(
    report: dict[str, Any],
    dataset_path: Path = DEFAULT_SAMPLE_DATASET,
) -> int:
    """Write fresh realtime values back into sample-dataset.lof_realtime.

    The local API computes premium_nav = (price - nav_official) / nav_official.
    Live price/iopv come from the JSONL snapshot, but nav_official used to stay
    at the static 6/18 placeholder, making premium_nav wildly off. Here we push
    the fundgz-derived nav_official (dwjz) + nav_official_date (jzrq) alongside
    price/iopv/premium so premium_nav stays in the same time-frame as price.

    Only codes present in both the report and the dataset get updated; others
    keep their previous values. ?6 field names are unchanged (no CCR).
    """
    if not dataset_path.exists():
        return 0
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    by_code = {item["code"]: item for item in report.get("items", [])}
    ts = report.get("ts")
    updated = 0
    for row in dataset.get("lof_realtime", []):
        item = by_code.get(row.get("code"))
        if not item:
            continue
        if ts:
            row["ts"] = ts
        for key in REALTIME_REFRESH_KEYS:
            if key not in item:
                continue
            # Live fields always reflect the real source (null if unavailable);
            # other fields keep their previous value on a transient null so we
            # never wipe good data (e.g. nav_official on a one-off fundgz miss).
            if item[key] is not None or key in REALTIME_OVERWRITE_NULL_KEYS:
                row[key] = item[key]
        updated += 1
    dataset_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return updated


def run_watchlist_long_run(
    duration_minutes: float,
    interval_seconds: float,
    output_dir: str | Path,
    snapshot_file: str | Path,
    metas: list[LofMeta] | None = None,
    iterations: int | None = None,
    ts_start: str | None = None,
    sleeper: Callable[[float], None] | None = None,
    now: Callable[[], datetime] | None = None,
    payload_provider: Callable[[list[LofMeta]], dict[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    metas = metas or load_default_watchlist()
    sleeper = sleeper or time.sleep
    now_fn = now or (lambda: datetime.now().astimezone())
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    snapshot_path = Path(snapshot_file)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    payload_provider = payload_provider or fetch_watchlist_payloads

    started_at = now_fn()
    started_iso = ts_start or started_at.isoformat(timespec="seconds")
    deadline = (
        started_at + timedelta(minutes=duration_minutes)
        if duration_minutes > 0
        else None
    )

    iteration = 0
    last_report: dict[str, Any] | None = None
    aggregator = StabilityAggregator(metas)
    failure_streak: dict[str, int] = {}

    while True:
        iteration += 1
        loop_ts = (
            ts_start if iteration == 1 and ts_start
            else now_fn().isoformat(timespec="seconds")
        )
        payloads = payload_provider(metas)
        report = build_watchlist_report(metas, payloads, ts=loop_ts)
        # PRD M2-B: 连续两分钟 degraded 升级 stale；ok 即清零。
        for item in report["items"]:
            code = item["code"]
            if item["source_quality"] == "ok":
                failure_streak[code] = 0
                continue
            failure_streak[code] = failure_streak.get(code, 0) + 1
            if failure_streak[code] >= 2:
                item["source_quality"] = "stale"
                tail = f"stale_consecutive_failures:{failure_streak[code]}"
                item["failure_reason"] = ";".join(
                    filter(None, [item.get("failure_reason") or "", tail])
                )
        target_count = report["summary"]["target_count"]
        ok_count = sum(1 for it in report["items"] if it["source_quality"] == "ok")
        degraded_count = sum(1 for it in report["items"] if it["source_quality"] == "degraded")
        stale_count = sum(1 for it in report["items"] if it["source_quality"] == "stale")
        report["summary"]["ok_count"] = ok_count
        report["summary"]["degraded_count"] = degraded_count
        report["summary"]["stale_count"] = stale_count
        report["summary"]["field_completeness"] = round(ok_count / target_count, 6) if target_count else 0.0

        write_watchlist_outputs(report, output_root, snapshot_path)
        aggregator.consume(report)
        last_report = report

        reached_iter = iterations is not None and iteration >= iterations
        reached_time = deadline is not None and now_fn() >= deadline
        if reached_iter or reached_time:
            break
        sleeper(max(0.0, interval_seconds))

    ended_at = now_fn()
    stability = aggregator.finalize()

    long_run_summary: dict[str, Any] = {
        "iterations": iteration,
        "started_at": started_iso,
        "ended_at": ended_at.isoformat(timespec="seconds"),
        "duration_seconds": int((ended_at - started_at).total_seconds()),
        "interval_seconds": interval_seconds,
        "snapshot_file": str(snapshot_path),
        "report_file": str(output_root / DEFAULT_REPORT_NAME),
        "stability_md": str(output_root / DEFAULT_STABILITY_NAME),
        "stability_json": str(output_root / DEFAULT_STABILITY_JSON),
        "target_count": stability["target_count"],
        "ok_total": stability["ok_total"],
        "degraded_total": stability["degraded_total"],
        "stale_total": stability["stale_total"],
        "elapsed_total_ms": stability["elapsed_total_ms"],
        "last_summary": last_report["summary"] if last_report else None,
    }
    long_run_path = output_root / DEFAULT_LONG_RUN_NAME
    long_run_path.write_text(json.dumps(long_run_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    stability_payload = {
        "iterations": iteration,
        "started_at": started_iso,
        "ended_at": ended_at.isoformat(timespec="seconds"),
        "interval_seconds": interval_seconds,
        "summary": stability["summary"],
        "items": stability["items"],
    }
    stability_json_path = output_root / DEFAULT_STABILITY_JSON
    stability_json_path.write_text(json.dumps(stability_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    stability_md_path = output_root / DEFAULT_STABILITY_NAME
    stability_md_path.write_text(_render_stability_md(long_run_summary, stability_payload), encoding="utf-8")

    long_run_summary["stability_md_file"] = str(stability_md_path)
    long_run_summary["stability_json_file"] = str(stability_json_path)
    return long_run_summary


class StabilityAggregator:
    def __init__(self, metas: list[LofMeta]) -> None:
        self._meta_by_code = {meta.code: meta for meta in metas}
        self._iterations = 0
        self._ok_total = 0
        self._degraded_total = 0
        self._stale_total = 0
        self._elapsed_total_ms = 0
        self._items: dict[str, dict[str, Any]] = {
            meta.code: {
                "code": meta.code,
                "name": meta.name,
                "type": meta.type,
                "status": meta.status,
                "scale_yi": meta.scale_yi,
                "ok": 0,
                "degraded": 0,
                "stale": 0,
                "samples": 0,
                "elapsed_ms_total": 0,
                "primary_source_hits": {},
                "backup_source_hits": {},
                "failure_reasons": {},
                "source_quality_last": "",
            }
            for meta in metas
        }

    def consume(self, report: dict[str, Any]) -> None:
        self._iterations += 1
        for item in report["items"]:
            code = item["code"]
            slot = self._items.get(code)
            if slot is None:
                continue
            slot["samples"] += 1
            quality = item["source_quality"]
            slot[quality] = slot.get(quality, 0) + 1
            slot["source_quality_last"] = quality
            slot["elapsed_ms_total"] += int(item.get("elapsed_ms") or 0)
            primary = item.get("primary_price_source") or ""
            if primary:
                slot["primary_source_hits"][primary] = slot["primary_source_hits"].get(primary, 0) + 1
            for attempt in item.get("price_attempts") or []:
                if attempt.get("hit"):
                    name = attempt.get("source") or ""
                    if name:
                        slot["backup_source_hits"][name] = slot["backup_source_hits"].get(name, 0) + 1
            reason = item.get("failure_reason") or ""
            if reason:
                slot["failure_reasons"][reason] = slot["failure_reasons"].get(reason, 0) + 1
            if quality == "ok":
                self._ok_total += 1
            elif quality == "degraded":
                self._degraded_total += 1
            elif quality == "stale":
                self._stale_total += 1

    def finalize(self) -> dict[str, Any]:
        target_count = len(self._items)
        items: list[dict[str, Any]] = []
        for code, slot in self._items.items():
            samples = slot["samples"] or 1
            ok_ratio = round(slot["ok"] / samples, 6)
            avg_elapsed = round(slot["elapsed_ms_total"] / samples, 2)
            recommendation = _recommend(slot)
            items.append(
                {
                    **slot,
                    "ok_ratio": ok_ratio,
                    "avg_elapsed_ms": avg_elapsed,
                    "recommendation": recommendation,
                }
            )
        items.sort(key=lambda x: (x["recommendation"], x["ok_ratio"], x["code"]))
        keep = sum(1 for it in items if it["recommendation"] == "keep")
        watch = sum(1 for it in items if it["recommendation"] == "watch")
        replace = sum(1 for it in items if it["recommendation"] == "replace")
        summary = {
            "target_count": target_count,
            "iterations": self._iterations,
            "ok_total": self._ok_total,
            "degraded_total": self._degraded_total,
            "stale_total": self._stale_total,
            "elapsed_total_ms": self._elapsed_total_ms,
            "keep_count": keep,
            "watch_count": watch,
            "replace_count": replace,
        }
        return {
            "target_count": target_count,
            "ok_total": self._ok_total,
            "degraded_total": self._degraded_total,
            "stale_total": self._stale_total,
            "elapsed_total_ms": self._elapsed_total_ms,
            "summary": summary,
            "items": items,
        }


def _recommend(slot: dict[str, Any]) -> str:
    samples = slot["samples"]
    if samples == 0:
        return "watch"
    ok_ratio = slot["ok"] / samples
    if ok_ratio >= 0.95:
        return "keep"
    if ok_ratio >= 0.80:
        return "watch"
    return "replace"


def _render_stability_md(long_run: dict[str, Any], stability: dict[str, Any]) -> str:
    summary = stability["summary"]
    lines: list[str] = []
    lines.append("# 30 只 watchlist-v2 长跑稳定性结论")
    lines.append("")
    lines.append(f"- 时间窗：{long_run['started_at']} ~ {long_run['ended_at']}")
    lines.append(f"- 迭代次数：{summary['iterations']}")
    lines.append(f"- 总样本：{summary['target_count']} 只 × {summary['iterations']} 次")
    lines.append(
        f"- 累计 ok={summary['ok_total']}，degraded={summary['degraded_total']}，stale={summary['stale_total']}"
    )
    lines.append(
        f"- 推荐分布：keep={summary['keep_count']}，watch={summary['watch_count']}，replace={summary['replace_count']}"
    )
    lines.append("")
    lines.append("## 单只稳定性")
    lines.append("")
    lines.append(
        "| code | name | type | status | scale_yi | ok_ratio | avg_elapsed_ms | primary_source_hits | failure_reasons | recommendation |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for item in stability["items"]:
        primary = ",".join(
            f"{name}:{count}" for name, count in sorted(item["primary_source_hits"].items())
        ) or "-"
        reasons = ",".join(
            f"{name}:{count}" for name, count in sorted(item["failure_reasons"].items())
        ) or "-"
        lines.append(
            "| {code} | {name} | {type} | {status} | {scale_yi} | {ok_ratio} | {avg} | {primary} | {reasons} | {rec} |".format(
                code=item["code"],
                name=item["name"].replace("|", "\\|"),
                type=item["type"],
                status=item["status"],
                scale_yi=item["scale_yi"],
                ok_ratio=item["ok_ratio"],
                avg=item["avg_elapsed_ms"],
                primary=primary,
                reasons=reasons,
                rec=item["recommendation"],
            )
        )
    lines.append("")
    lines.append("## 处理建议口径")
    lines.append("")
    lines.append("- keep：ok_ratio ≥ 0.95，主源稳定命中，无显著失败；可全量保留。")
    lines.append("- watch：0.80 ≤ ok_ratio < 0.95，存在偶发降级，建议交易日复跑确认。")
    lines.append("- replace：ok_ratio < 0.80，主源持续失败，建议进入 watchlist-v2.1 评审替换。")
    lines.append("")
    lines.append("## 约束")
    lines.append("")
    lines.append("- 仅本地真实采集，不打 next.bspapp.com，不消耗线上 RU/WU。")
    lines.append("- §6 字段未变更；snapshot JSONL 仍只暴露 code/price/iopv/premium/coverage/source_quality。")
    lines.append("- 长跑 stale 计数沿用 PRD §M2-B 连续两分钟失败口径。")
    lines.append("")
    return "\n".join(lines)


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


def _primary_source_hit(attempts: list[dict[str, Any]]) -> str:
    for attempt in attempts:
        if attempt.get("hit"):
            return attempt.get("source") or ""
    return ""
