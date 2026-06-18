from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from loguru import logger

from fetcher.pipeline.quota import write_quota_report
from fetcher.pipeline.real_poc import build_poc_report, write_poc_outputs
from fetcher.pipeline.retry_trace import build_retry_trace_samples
from fetcher.pipeline.snapshot import write_sample_outputs
from fetcher.sources.csv_assets import load_benchmark_mapping, load_watchlist


def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "sample-output":
        files = write_sample_outputs(args.output_dir, args.ts)
        for name, path in files.items():
            logger.info("wrote {} sample to {}", name, path)
        return

    if args.command == "real-poc":
        report = build_poc_report(ts=args.ts)
        files = write_poc_outputs(report, args.output_dir, args.snapshot_file)
        logger.info("real POC summary: {}", report["summary"])
        for name, path in files.items():
            logger.info("wrote real POC {} to {}", name, path)
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

    evidence = subparsers.add_parser("ac-evidence", help="write AC-C2 retry trace and AC-S1 quota estimate")
    evidence.add_argument("--output-dir", type=Path, default=Path("../outputs"))

    return parser


if __name__ == "__main__":
    main()
