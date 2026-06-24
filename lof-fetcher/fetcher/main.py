from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from loguru import logger

from fetcher.pipeline.quota import write_quota_report
from fetcher.pipeline.real_poc import build_poc_report, run_long_run, write_poc_outputs
from fetcher.pipeline.real_watchlist import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SNAPSHOT_NAME,
    DEFAULT_WATCHLIST_PATH,
    build_watchlist_report,
    fetch_watchlist_payloads,
    load_watchlist,
    run_watchlist_long_run,
    update_sample_dataset_realtime,
    write_watchlist_outputs,
)
from fetcher.pipeline.holdings_refresh import (
    run_holdings_refresh,
)
from fetcher.pipeline.history_backfill import DEFAULT_HISTORY_FILE, run_history_backfill
from fetcher.pipeline.daemon import run_daemon
from fetcher.pipeline.subscribe_refresh import run_subscribe_status_refresh
from fetcher.pipeline.shares_confirm_refresh import run_shares_confirm_refresh
from fetcher.pipeline import process_control as pc
from fetcher.pipeline.retry_trace import build_retry_trace_samples
from fetcher.pipeline.snapshot import write_sample_outputs
from fetcher.sources.csv_assets import load_benchmark_mapping


def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "sample-output":
        files = write_sample_outputs(args.output_dir, args.ts)
        for name, path in files.items():
            logger.info("wrote {} sample to {}", name, path)
        return

    if args.command == "real-poc":
        if args.duration_minutes and args.duration_minutes > 0:
            summary = run_long_run(
                duration_minutes=args.duration_minutes,
                interval_seconds=args.interval_seconds,
                output_dir=args.output_dir,
                snapshot_file=args.snapshot_file,
                ts_start=args.ts,
            )
            logger.info("real POC long-run summary: {}", summary)
            return
        report = build_poc_report(ts=args.ts)
        files = write_poc_outputs(report, args.output_dir, args.snapshot_file)
        logger.info("real POC summary: {}", report["summary"])
        for name, path in files.items():
            logger.info("wrote real POC {} to {}", name, path)
        return

    if args.command == "real-watchlist":
        metas = load_watchlist(args.watchlist)
        if args.duration_minutes and args.duration_minutes > 0:
            summary = run_watchlist_long_run(
                duration_minutes=args.duration_minutes,
                interval_seconds=args.interval_seconds,
                output_dir=args.output_dir,
                snapshot_file=args.snapshot_file,
                metas=metas,
                ts_start=args.ts,
            )
            logger.info("real watchlist long-run summary: {}", summary)
            return
        from datetime import datetime
        ts = args.ts or datetime.now().astimezone().isoformat(timespec="seconds")
        payloads = fetch_watchlist_payloads(metas)
        report = build_watchlist_report(metas, payloads, ts=ts)
        files = write_watchlist_outputs(report, args.output_dir, args.snapshot_file)
        update_sample_dataset_realtime(report)
        logger.info("real watchlist summary: {}", report["summary"])
        for name, path in files.items():
            logger.info("wrote real watchlist {} to {}", name, path)
        return

    if args.command == "holdings-refresh":
        payload = run_holdings_refresh(
            output_dir=args.output_dir,
            ts=args.ts,
            with_realtime=not args.no_realtime,
            write_dataset=not args.no_dataset,
        )
        logger.info("holdings refresh summary: {}", payload["summary"])
        return

    if args.command == "daemon":
        if args.status:
            info = pc.status(args.pid_file)
            logger.info("daemon status: {}", info)
            return
        if args.stop:
            result = pc.stop_daemon(args.pid_file, args.stop_file, timeout_seconds=args.stop_timeout)
            logger.info("daemon stop result: {}", result)
            return
        summary = run_daemon(
            output_dir=args.output_dir,
            snapshot_file=args.snapshot_file,
            trading_interval_seconds=args.interval_seconds,
            idle_interval_seconds=args.idle_interval_seconds,
            with_holdings=not args.no_holdings,
            with_subscribe_status=not args.no_subscribe_status,
            with_shares_confirm=not args.no_shares_confirm,
            max_iterations=args.max_iterations if args.max_iterations and args.max_iterations > 0 else None,
            pid_file=args.pid_file,
            stop_file=args.stop_file,
            log_file=args.log_file,
        )
        logger.info("daemon stopped summary: {}", summary)
        return

    if args.command == "subscribe-refresh":
        result = run_subscribe_status_refresh(
            write_dataset=not args.no_dataset,
            codes=args.codes or None,
        )
        logger.info(
            "subscribe-status refresh: updated={} by_source={} limited_with_amount={}",
            result["updated"], result["by_source"], result["limited_with_amount"],
        )
        return

    if args.command == "shares-confirm-refresh":
        result = run_shares_confirm_refresh(
            write_dataset=not args.no_dataset,
            codes=args.codes or None,
        )
        logger.info(
            "shares/confirm refresh: updated={} shares_coverage={} confirm_coverage={} cookie_present={}",
            result["updated"], result["shares_coverage"],
            result["confirm_coverage"], result["cookie_present"],
        )
        return

    if args.command == "history-backfill":
        metas = load_watchlist(args.watchlist)
        codes = [m.code for m in metas]
        history_path = args.history_file or (args.output_dir / DEFAULT_HISTORY_FILE)
        summary = run_history_backfill(codes, history_path, limit=args.limit)
        logger.info(
            "history backfill: {} records across {} codes ({} with 30d pctile) -> {}",
            summary["total_records"], summary["target_count"], summary["codes_with_pctile"], summary["history_file"],
        )
        for entry in summary["per_code"]:
            logger.info(
                "  {} close={} nav={} trading_days={} valid_premium={} {}",
                entry["code"], entry["close_source"] or "MISS", entry["nav_source"] or "MISS",
                entry["trading_days"], entry["valid_premium_days"],
                (entry["close_error"] or entry["nav_error"] or ""),
            )
        return

    if args.command == "ac-evidence":
        files = build_retry_trace_samples(args.output_dir)
        quota_path = write_quota_report(args.output_dir / "backend-ac-s1-quota-estimate-v2.json")
        for name, path in files.items():
            logger.info("wrote retry {} trace to {}", name, path)
        logger.info("wrote quota estimate to {}", quota_path)
        return

    from fetcher.config import get_settings

    settings = get_settings()
    watchlist = load_watchlist(settings.watchlist_path)
    benchmark_mapping = load_benchmark_mapping(settings.benchmark_mapping_path)
    logger.info("loaded watchlist={} benchmark_codes={}", len(watchlist), len(benchmark_mapping))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LOF fetcher utility commands")
    subparsers = parser.add_subparsers(dest="command")

    sample = subparsers.add_parser("sample-output", help="write v2 realtime/API sample JSON files")
    sample.add_argument("--output-dir", type=Path, default=Path("../outputs"))
    sample.add_argument("--ts", default="2026-06-18T10:31:00+08:00")

    real_poc = subparsers.add_parser("real-poc", help="run M3 real-market POC for the approved 5 LOF codes")
    real_poc.add_argument("--output-dir", type=Path, default=Path("../outputs"))
    real_poc.add_argument("--snapshot-file", type=Path, default=Path("../outputs/local-minute-snapshots-v2.jsonl"))
    real_poc.add_argument("--ts", default=None)
    real_poc.add_argument("--duration-minutes", type=float, default=0.0,
                          help="run periodically for N minutes (long-run mode); 0 = single shot")
    real_poc.add_argument("--interval-seconds", type=float, default=60.0,
                          help="seconds between iterations in long-run mode")

    watchlist = subparsers.add_parser(
        "real-watchlist",
        help="run real-market collection across the full watchlist-v2 (30 codes)",
    )
    watchlist.add_argument("--output-dir", type=Path, default=Path("../outputs"))
    watchlist.add_argument(
        "--snapshot-file",
        type=Path,
        default=Path("../outputs/local-minute-snapshots-watchlist-v2.jsonl"),
    )
    watchlist.add_argument("--watchlist", type=Path, default=DEFAULT_WATCHLIST_PATH)
    watchlist.add_argument("--ts", default=None)
    watchlist.add_argument("--duration-minutes", type=float, default=0.0)
    watchlist.add_argument("--interval-seconds", type=float, default=60.0)

    holdings = subparsers.add_parser(
        "holdings-refresh",
        help="fetch real quarterly top-10 holdings + live change pct for watchlist-v2",
    )
    holdings.add_argument("--output-dir", type=Path, default=Path("../outputs"))
    holdings.add_argument("--ts", default=None)
    holdings.add_argument("--no-realtime", action="store_true", help="skip live stock change pct")
    holdings.add_argument("--no-dataset", action="store_true", help="do not write sample-dataset.json")

    daemon = subparsers.add_parser(
        "daemon",
        help="resident minute-level collector: trading hours collect every 60s, idle sleep",
    )
    daemon.add_argument("--output-dir", type=Path, default=Path("../outputs"))
    daemon.add_argument("--snapshot-file", type=Path, default=None,
                        help="JSONL appended each minute; default outputs/local-minute-snapshots-watchlist-v2.jsonl")
    daemon.add_argument("--interval-seconds", type=float, default=60.0,
                        help="collection interval during trading hours")
    daemon.add_argument("--idle-interval-seconds", type=float, default=300.0,
                        help="poll interval outside trading hours (no collection)")
    daemon.add_argument("--no-holdings", action="store_true",
                        help="skip per-minute holdings change-pct overlay")
    daemon.add_argument("--no-subscribe-status", action="store_true",
                        help="skip the once-per-day subscribe/redeem status + limit refresh (PRD 1.3)")
    daemon.add_argument("--no-shares-confirm", action="store_true",
                        help="skip the once-per-day on-exchange shares + confirm-day refresh (PRD 1.4)")
    daemon.add_argument("--max-iterations", type=int, default=0,
                        help="TEST ONLY: stop after N loop ticks (0=unbounded)")
    daemon.add_argument("--pid-file", type=Path, default=pc.DEFAULT_PID_FILE,
                        help="PID file for single-instance enforcement (default outputs/daemon.pid)")
    daemon.add_argument("--stop-file", type=Path, default=pc.DEFAULT_STOP_FILE,
                        help="stop-flag file polled by the running daemon (default outputs/daemon.stop)")
    daemon.add_argument("--log-file", type=Path, default=Path("logs/daemon.log"),
                        help="rotating file log sink (default logs/daemon.log; console kept)")
    daemon.add_argument("--status", action="store_true",
                        help="report whether a daemon is running (PID + start time) and exit")
    daemon.add_argument("--stop", action="store_true",
                        help="gracefully stop a running daemon and exit")
    daemon.add_argument("--stop-timeout", type=float, default=30.0,
                        help="seconds to wait for graceful stop before force terminate")

    history = subparsers.add_parser(
        "history-backfill",
        help="backfill real daily history (eastmoney/tencent kline + ttjj LSJZ) with 30d percentile",
    )
    history.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    history.add_argument("--watchlist", type=Path, default=DEFAULT_WATCHLIST_PATH)
    history.add_argument("--history-file", type=Path, default=None,
                         help="JSONL sedimentation file; default outputs/local-history-daily-v2.jsonl")
    history.add_argument("--limit", type=int, default=60,
                         help="max trading days fetched per source (>=30 recommended)")

    sub_refresh = subparsers.add_parser(
        "subscribe-refresh",
        help="refresh daily subscribe/redeem status + subscribe-limit into lof_meta (PRD 1.3)",
    )
    sub_refresh.add_argument("--no-dataset", action="store_true", help="do not write sample-dataset.json")
    sub_refresh.add_argument("--codes", nargs="*", default=None, help="optional explicit code subset")

    shares_refresh = subparsers.add_parser(
        "shares-confirm-refresh",
        help="refresh daily on-exchange shares + open-end confirm days into lof_meta (PRD 1.4)",
    )
    shares_refresh.add_argument("--no-dataset", action="store_true", help="do not write sample-dataset.json")
    shares_refresh.add_argument("--codes", nargs="*", default=None, help="optional explicit code subset")

    evidence = subparsers.add_parser("ac-evidence", help="write AC-C2 retry trace and AC-S1 quota estimate")
    evidence.add_argument("--output-dir", type=Path, default=Path("../outputs"))

    return parser


if __name__ == "__main__":
    main()
