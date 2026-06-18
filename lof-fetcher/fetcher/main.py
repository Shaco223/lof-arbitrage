from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from loguru import logger

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

    return parser


if __name__ == "__main__":
    main()
