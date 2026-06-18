from __future__ import annotations

import json
import sys
from pathlib import Path

FETCHER_ROOT = Path(__file__).resolve().parents[1]
if str(FETCHER_ROOT) not in sys.path:
    sys.path.insert(0, str(FETCHER_ROOT))

from fetcher.pipeline.snapshot import build_realtime_snapshot, build_sample_api_outputs, default_asset_paths
from fetcher.sources.csv_assets import load_benchmark_mapping, load_watchlist


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    watchlist_path, benchmark_path = default_asset_paths(PROJECT_ROOT / "lof-fetcher")
    snapshot = build_realtime_snapshot(watchlist_path, benchmark_path)
    samples = build_sample_api_outputs(watchlist_path, benchmark_path)
    watchlist = load_watchlist(watchlist_path)
    benchmark_mapping = load_benchmark_mapping(benchmark_path)

    realtime_by_code = {item["code"]: item for item in snapshot["items"]}
    lof_meta = []
    lof_holdings = []
    lof_history = []
    for meta in watchlist:
        realtime = realtime_by_code[meta.code]
        lof_meta.append(
            {
                "code": meta.code,
                "name": meta.name,
                "type": meta.type,
                "scale_yi": meta.scale_yi,
                "status": meta.status,
                "coverage_top10": realtime["coverage_breakdown"]["top10_weight"],
                "coverage_breakdown": realtime["coverage_breakdown"],
                "benchmark_raw": meta.benchmark_raw,
                "benchmark_components": [
                    {"index_code": component.index_code, "name": component.component_name, "weight": component.weight}
                    for component in benchmark_mapping.get(meta.code, [])
                ],
            }
        )
        for index in range(3):
            lof_holdings.append(
                {
                    "code": meta.code,
                    "report_date": "2026-03-31",
                    "stock_code": f"S{index + 1:05d}",
                    "stock_name": f"样例持仓{index + 1}",
                    "weight": round(0.08 - index * 0.01, 6),
                }
            )
        for history_item in samples["history"]["data"]["items"]:
            lof_history.append({"code": meta.code, **history_item})

    payload = {
        "ts": snapshot["ts"],
        "lof_meta": lof_meta,
        "lof_realtime": [
            {
                "code": item["code"],
                "ts": snapshot["ts"],
                "price": item["price"],
                "iopv": item["iopv"],
                "premium": item["premium"],
                "coverage": item["coverage"],
                "source_quality": item["source_quality"],
            }
            for item in snapshot["items"]
        ],
        "lof_history": lof_history,
        "lof_holdings": lof_holdings,
    }
    target = PROJECT_ROOT / "uniCloud-aliyun" / "tests" / "sample-dataset.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
