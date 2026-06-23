"""Resident minute-level collection daemon (PRD M2, Plan A simple version).

Keeps a long-running loop that, during trading hours, fetches the full 30-LOF
watchlist (market price + fundgz estimate) every 60s and re-overlays live stock
change pct onto the cached quarterly holdings, writing to the existing JSONL /
sample-dataset.json so local-api-server (127.0.0.1:8787) serves fresh data
without a restart.

Outside trading hours it sleeps (longer poll interval), only checking whether
trading has started; it does not collect and does not consume any source.

Robustness (Plan A minimum):
  - per-LOF failure -> skip, keep others, record degraded/stale (PRD 1.2.1
    availability-only rule; nav drift never degrades).
  - whole-iteration exception -> caught, logged, wait for next tick, no crash.
  - console/log shows each iteration time + ok/degraded/stale counts.

Not in scope (added at go-live): PID management, auto-start, log rotation.
"""
from __future__ import annotations

import time as _time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from loguru import logger

from fetcher.pipeline.holdings_refresh import (
    DEFAULT_SAMPLE_DATASET,
    build_holdings_payload,
    overlay_realtime_on_holdings,
    update_sample_dataset_holdings,
    write_holdings_outputs,
)
from fetcher.pipeline.real_watchlist import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SNAPSHOT_NAME,
    build_watchlist_report,
    fetch_watchlist_payloads,
    load_default_watchlist,
    update_sample_dataset_realtime,
    write_watchlist_outputs,
)
from fetcher.scheduler import CN_TZ, is_trading_time
from fetcher.sources.csv_assets import LofMeta

DEFAULT_TRADING_INTERVAL_SECONDS = 60.0
DEFAULT_IDLE_INTERVAL_SECONDS = 300.0
DEFAULT_HOLDINGS_REFRESH_SECONDS = 3600.0


def _now() -> datetime:
    return datetime.now(CN_TZ)


def _escalate_consecutive_failures(
    report: dict[str, Any],
    failure_streak: dict[str, int],
) -> dict[str, Any]:
    """PRD M2-B: two consecutive non-ok minutes escalate degraded -> stale."""
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
    target = report["summary"]["target_count"]
    ok = sum(1 for it in report["items"] if it["source_quality"] == "ok")
    degraded = sum(1 for it in report["items"] if it["source_quality"] == "degraded")
    stale = sum(1 for it in report["items"] if it["source_quality"] == "stale")
    report["summary"]["ok_count"] = ok
    report["summary"]["degraded_count"] = degraded
    report["summary"]["stale_count"] = stale
    report["summary"]["field_completeness"] = round(ok / target, 6) if target else 0.0
    return report


def run_daemon(
    *,
    metas: list[LofMeta] | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    snapshot_file: str | Path | None = None,
    dataset_path: Path = DEFAULT_SAMPLE_DATASET,
    trading_interval_seconds: float = DEFAULT_TRADING_INTERVAL_SECONDS,
    idle_interval_seconds: float = DEFAULT_IDLE_INTERVAL_SECONDS,
    holdings_refresh_seconds: float = DEFAULT_HOLDINGS_REFRESH_SECONDS,
    with_holdings: bool = True,
    max_iterations: int | None = None,
    sleeper: Callable[[float], None] | None = None,
    now: Callable[[], datetime] | None = None,
    trading_check: Callable[[datetime], bool] | None = None,
    payload_provider: Callable[[list[LofMeta]], dict[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Run the resident collection loop.

    max_iterations is a TEST/SMOKE convenience only; production runs leave it
    None for an unbounded loop (Ctrl+C / SIGINT to stop).
    """
    metas = metas or load_default_watchlist()
    sleeper = sleeper or _time.sleep
    now_fn = now or _now
    trading_fn = trading_check or is_trading_time
    payload_provider = payload_provider or fetch_watchlist_payloads
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    snapshot_path = Path(snapshot_file) if snapshot_file else output_root / DEFAULT_SNAPSHOT_NAME
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    failure_streak: dict[str, int] = {}
    cached_holdings: list[dict[str, Any]] | None = None
    cached_per_lof: list[dict[str, Any]] | None = None
    last_holdings_at: datetime | None = None

    collect_iterations = 0
    idle_iterations = 0
    error_iterations = 0
    last_summary: dict[str, Any] | None = None
    started_at = now_fn()
    logger.info(
        "daemon started metas={} trading_interval={}s idle_interval={}s",
        len(metas), trading_interval_seconds, idle_interval_seconds,
    )

    total_iterations = 0
    while True:
        moment = now_fn()
        trading = trading_fn(moment)
        if not trading:
            idle_iterations += 1
            logger.info(
                "[{}] non-trading hours -> sleep {}s (no collection)",
                moment.isoformat(timespec="seconds"), idle_interval_seconds,
            )
            total_iterations += 1
            if max_iterations is not None and total_iterations >= max_iterations:
                break
            sleeper(max(0.0, idle_interval_seconds))
            continue

        try:
            loop_ts = moment.isoformat(timespec="seconds")
            payloads = payload_provider(metas)
            report = build_watchlist_report(metas, payloads, ts=loop_ts)
            report = _escalate_consecutive_failures(report, failure_streak)
            write_watchlist_outputs(report, output_root, snapshot_path)
            # Push fresh nav_official/nav_official_date (+price/iopv/premium) back into
            # sample-dataset so the local API computes premium_nav with a NAV in the
            # same time-frame as the live price (fixes premium_nav decoupling).
            update_sample_dataset_realtime(report, dataset_path)

            if with_holdings:
                need_full = (
                    cached_holdings is None
                    or last_holdings_at is None
                    or (moment - last_holdings_at).total_seconds() >= holdings_refresh_seconds
                )
                if need_full:
                    full = build_holdings_payload(metas, ts=loop_ts, with_realtime=True)
                    cached_holdings = full["holdings"]
                    cached_per_lof = full["per_lof"]
                    last_holdings_at = moment
                    holdings_payload = full
                else:
                    holdings_payload = overlay_realtime_on_holdings(
                        cached_holdings, cached_per_lof, ts=loop_ts, with_realtime=True
                    )
                write_holdings_outputs(holdings_payload, output_root)
                update_sample_dataset_holdings(holdings_payload, dataset_path)

            collect_iterations += 1
            summary = report["summary"]
            last_summary = summary
            logger.info(
                "[{}] collected ok={} degraded={} stale={} completeness={}",
                loop_ts, summary.get("ok_count"), summary.get("degraded_count"),
                summary.get("stale_count"), summary.get("field_completeness"),
            )
        except Exception as exc:  # noqa: BLE001 - daemon must not crash on a bad tick
            error_iterations += 1
            logger.exception("[{}] iteration failed, will retry next tick: {}",
                             now_fn().isoformat(timespec="seconds"), exc)

        total_iterations += 1
        if max_iterations is not None and total_iterations >= max_iterations:
            break
        sleeper(max(0.0, trading_interval_seconds))

    ended_at = now_fn()
    return {
        "started_at": started_at.isoformat(timespec="seconds"),
        "ended_at": ended_at.isoformat(timespec="seconds"),
        "total_iterations": total_iterations,
        "collect_iterations": collect_iterations,
        "idle_iterations": idle_iterations,
        "error_iterations": error_iterations,
        "snapshot_file": str(snapshot_path),
        "last_summary": last_summary,
    }
