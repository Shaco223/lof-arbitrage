from __future__ import annotations

from loguru import logger

from fetcher.config import get_settings
from fetcher.sources.csv_assets import load_benchmark_mapping, load_watchlist


def main() -> None:
    settings = get_settings()
    watchlist = load_watchlist(settings.watchlist_path)
    benchmark_mapping = load_benchmark_mapping(settings.benchmark_mapping_path)
    logger.info("loaded watchlist={} benchmark_codes={}", len(watchlist), len(benchmark_mapping))


if __name__ == "__main__":
    main()
