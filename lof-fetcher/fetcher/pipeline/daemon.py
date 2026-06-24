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

Go-live robustness (this revision): single-instance PID file with command-
line/create-time verification (Windows PID-reuse safe), graceful --stop via
a stop-flag file, --status query, and rotating file logging. OS-level
auto-start on boot is still out of scope (documented in the runbook).
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
from fetcher.pipeline.history_backfill import (
    DEFAULT_HISTORY_FILE,
    append_close_estimates,
)
from fetcher.pipeline.subscribe_refresh import run_subscribe_status_refresh
from fetcher.pipeline import process_control as pc
from fetcher.scheduler import CN_TZ, is_trading_time
from fetcher.sources.csv_assets import LofMeta

DEFAULT_TRADING_INTERVAL_SECONDS = 60.0
DEFAULT_IDLE_INTERVAL_SECONDS = 300.0
DEFAULT_HOLDINGS_REFRESH_SECONDS = 3600.0
DEFAULT_LOG_FILE = Path("logs/daemon.log")
DEFAULT_LOG_ROTATION = "10 MB"
DEFAULT_LOG_RETENTION = 7
DEFAULT_STOP_POLL_SECONDS = 1.0


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


def _add_file_log_sink(
    log_file: Path,
    *,
    rotation: str = DEFAULT_LOG_ROTATION,
    retention: int = DEFAULT_LOG_RETENTION,
) -> int | None:
    """Add a rotating file sink to loguru (console sink is left intact).

    Returns the sink id so the caller can remove it on exit; None if disabled.
    """
    if log_file is None:
        return None
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return logger.add(
        str(log_path),
        rotation=rotation,
        retention=retention,
        enqueue=True,
        encoding="utf-8",
        level="INFO",
    )


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
    with_subscribe_status: bool = True,
    history_file: str | Path | None = None,
    sediment_close_history: bool = True,
    max_iterations: int | None = None,
    pid_file: Path | None = pc.DEFAULT_PID_FILE,
    stop_file: Path | None = pc.DEFAULT_STOP_FILE,
    log_file: Path | None = DEFAULT_LOG_FILE,
    enforce_singleton: bool = True,
    stop_poll_seconds: float = DEFAULT_STOP_POLL_SECONDS,
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

    # --- Single-instance enforcement (avoids the repeatedly-hit stale-process
    # bug where an old daemon keeps writing the JSONL the front-end reads). ---
    if enforce_singleton and pid_file is not None:
        existing = pc.read_pid_file(pid_file)
        if pc.is_running(existing):
            raise RuntimeError(
                f"daemon already running (pid={existing.pid}, started_at={existing.started_at}); "
                f"use 'daemon --stop' or 'daemon --status' first"
            )
        # Stale pid file from a crashed/killed process: clear it and continue.
        pc.clear_pid_file(pid_file)
    # A leftover stop flag from a previous run must not stop us immediately.
    if stop_file is not None:
        pc.clear_stop_flag(stop_file)

    log_sink_id = _add_file_log_sink(log_file) if log_file is not None else None
    if pid_file is not None:
        pc.write_pid_file(pid_file, snapshot_file=str(snapshot_path))

    stopped_by_flag = False
    failure_streak: dict[str, int] = {}
    cached_holdings: list[dict[str, Any]] | None = None
    cached_per_lof: list[dict[str, Any]] | None = None
    last_holdings_at: datetime | None = None
    # Daily-class subscribe/redeem status + subscribe-limit (PRD 1.3): refresh at
    # most once per calendar day into lof_meta (NOT into the minute snapshot).
    subscribe_refresh_date: str | None = None
    history_path = Path(history_file) if history_file else output_root / DEFAULT_HISTORY_FILE
    # PRD 1.2.3: sediment the day's close-time premium_estimate_close exactly once,
    # on the trading -> non-trading transition (i.e. just after 15:00 close).
    last_report: dict[str, Any] | None = None
    last_report_date: str | None = None
    was_trading = False
    close_sediment_date: str | None = None

    collect_iterations = 0
    idle_iterations = 0
    error_iterations = 0
    last_summary: dict[str, Any] | None = None
    started_at = now_fn()
    logger.info(
        "daemon started metas={} trading_interval={}s idle_interval={}s",
        len(metas), trading_interval_seconds, idle_interval_seconds,
    )

    def _sleep_or_stop(seconds: float) -> bool:
        # Sleep in small slices so a stop flag is honored within ~stop_poll_seconds
        # instead of waiting the full 60s tick. Returns True if a stop was seen.
        if stop_file is None:
            sleeper(seconds)
            return False
        remaining = seconds
        slice_s = max(0.0, min(stop_poll_seconds, seconds)) if seconds > 0 else 0.0
        if slice_s <= 0:
            sleeper(seconds)
            return pc.stop_requested(stop_file)
        while remaining > 0:
            step = min(slice_s, remaining)
            sleeper(step)
            remaining -= step
            if pc.stop_requested(stop_file):
                return True
        return False

    total_iterations = 0
    try:
      while True:
        if stop_file is not None and pc.stop_requested(stop_file):
            stopped_by_flag = True
            logger.info("stop flag detected -> graceful shutdown")
            break
        moment = now_fn()
        trading = trading_fn(moment)
        if not trading:
            # Trading -> non-trading transition == market close: sediment the day's
            # close-time premium_estimate_close exactly once (PRD 1.2.3, append-only,
            # no backfill). premium_deviation stays null until T+1 official nav.
            if (
                sediment_close_history
                and was_trading
                and last_report is not None
                and last_report_date is not None
                and close_sediment_date != last_report_date
            ):
                try:
                    estimates = {
                        it["code"]: it.get("premium")
                        for it in last_report.get("items", [])
                    }
                    result = append_close_estimates(history_path, last_report_date, estimates)
                    close_sediment_date = last_report_date
                    logger.info(
                        "[{}] close sediment: appended {} premium_estimate_close for {} -> {}",
                        moment.isoformat(timespec="seconds"), result["appended"],
                        last_report_date, result["history_file"],
                    )
                except Exception as exc:  # noqa: BLE001 - close sediment must not crash daemon
                    logger.exception("close history sediment failed: {}", exc)
            was_trading = False
            idle_iterations += 1
            logger.info(
                "[{}] non-trading hours -> sleep {}s (no collection)",
                moment.isoformat(timespec="seconds"), idle_interval_seconds,
            )
            total_iterations += 1
            if max_iterations is not None and total_iterations >= max_iterations:
                break
            if _sleep_or_stop(max(0.0, idle_interval_seconds)):
                stopped_by_flag = True
                break
            continue

        try:
            loop_ts = moment.isoformat(timespec="seconds")
            payloads = payload_provider(metas)
            report = build_watchlist_report(metas, payloads, ts=loop_ts)
            report = _escalate_consecutive_failures(report, failure_streak)
            write_watchlist_outputs(report, output_root, snapshot_path)
            # Remember the freshest trading-day report so the close transition can
            # sediment its per-code premium (close-time price/IOPV-1) as the day's
            # premium_estimate_close (PRD 1.2.3).
            last_report = report
            last_report_date = moment.date().isoformat()
            was_trading = True
            # Push fresh nav_official/nav_official_date (+price/iopv/premium) back into
            # sample-dataset so the local API computes premium_nav with a NAV in the
            # same time-frame as the live price (fixes premium_nav decoupling).
            update_sample_dataset_realtime(report, dataset_path)

            # PRD 1.3: refresh daily subscribe/redeem status + subscribe-limit once
            # per calendar day (writes lof_meta, not the snapshot). Failures here
            # must never crash the minute loop.
            today = moment.date().isoformat()
            if with_subscribe_status and subscribe_refresh_date != today:
                try:
                    codes = [m.code for m in metas]
                    sub = run_subscribe_status_refresh(codes=codes, dataset_path=dataset_path)
                    subscribe_refresh_date = today
                    logger.info(
                        "[{}] subscribe-status daily refresh: updated={} by_source={} limited_with_amount={}",
                        loop_ts, sub.get("updated"), sub.get("by_source"), sub.get("limited_with_amount"),
                    )
                except Exception as exc:  # noqa: BLE001 - daily refresh must not crash daemon
                    logger.exception("subscribe-status daily refresh failed: {}", exc)

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
        if _sleep_or_stop(max(0.0, trading_interval_seconds)):
            stopped_by_flag = True
            break
    finally:
        if pid_file is not None:
            pc.clear_pid_file(pid_file)
        if stop_file is not None:
            pc.clear_stop_flag(stop_file)
        if log_sink_id is not None:
            try:
                logger.remove(log_sink_id)
            except Exception:
                pass

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
        "stopped_by_flag": stopped_by_flag,
    }
