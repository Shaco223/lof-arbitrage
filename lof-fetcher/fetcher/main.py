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
    write_watchlist_outputs,
)
from fetcher.pipeline.holdings_refresh import (
    run_holdings_refresh,
)
from fetcher.pipeline.daemon import run_daemon
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
        summary = run_daemon(
            output_dir=args.output_dir,
            snapshot_file=args.snapshot_file,
            trading_interval_seconds=args.interval_seconds,
            idle_interval_seconds=args.idle_interval_seconds,
            with_holdings=not args.no_holdings,
            max_iterations=args.max_iterations if args.max_iterations and args.max_iterations > 0 else None,
        )
        logger.info("daemon stopped summary: {}", summary)
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
    daemon.add_argument("--max-iterations", type=int, default=0,
                        help="TEST ONLY: stop after N loop ticks (0=unbounded)")

    evidence = subparsers.add_parser("ac-evidence", help="write AC-C2 retry trace and AC-S1 quota estimate")
    evidence.add_argument("--output-dir", type=Path, default=Path("../outputs"))

    return parser


if __name__ == "__main__":
    main()
