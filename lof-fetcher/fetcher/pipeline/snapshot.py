from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from fetcher.engine.coverage import CoverageInputs, calculate_coverage
from fetcher.engine.premium import calculate_premium
from fetcher.sources.csv_assets import BenchmarkComponent, benchmark_weights, load_benchmark_mapping, load_watchlist

DEFAULT_TS = "2026-06-18T10:31:00+08:00"


def default_asset_paths(fetcher_root: str | Path | None = None) -> tuple[Path, Path]:
    root = Path(fetcher_root) if fetcher_root else Path(__file__).resolve().parents[2]
    project_root = root.parent
    return project_root / "assets" / "lof-watchlist-v2.csv", project_root / "assets" / "benchmark-mapping-v2.csv"


def build_realtime_snapshot(
    watchlist_path: str | Path,
    benchmark_mapping_path: str | Path,
    ts: str = DEFAULT_TS,
) -> dict[str, Any]:
    watchlist = load_watchlist(watchlist_path)
    benchmark_mapping = load_benchmark_mapping(benchmark_mapping_path)
    items: list[dict[str, Any]] = []

    for index, meta in enumerate(watchlist):
        components = benchmark_mapping.get(meta.code, [])
        assigned_weight, cash_weight = benchmark_weights(components)
        top10_weight = _synthetic_top10_weight(meta.type, assigned_weight, index)
        coverage_result = calculate_coverage(
            CoverageInputs(
                fund_type=meta.type,
                top10_weight=top10_weight,
                benchmark_assigned_weight=assigned_weight,
                cash_weight=cash_weight,
            )
        )
        iopv = _synthetic_iopv(index)
        price = round(iopv * (1 + _synthetic_premium_seed(index)), 4)
        items.append(
            {
                "code": meta.code,
                "name": meta.name,
                "type": meta.type,
                "price": price,
                "iopv": iopv,
                "premium": calculate_premium(price, iopv),
                "coverage": coverage_result.coverage,
                "coverage_breakdown": {
                    "top10_weight": coverage_result.breakdown.top10_weight,
                    "benchmark_assigned_weight": coverage_result.breakdown.benchmark_assigned_weight,
                    "cash_weight": coverage_result.breakdown.cash_weight,
                },
                "pctile_30d": _synthetic_pctile(index),
                "source_quality": coverage_result.source_quality,
            }
        )

    return {"ts": ts, "items": items}


def build_sample_api_outputs(
    watchlist_path: str | Path,
    benchmark_mapping_path: str | Path,
    ts: str = DEFAULT_TS,
) -> dict[str, Any]:
    watchlist = load_watchlist(watchlist_path)
    benchmark_mapping = load_benchmark_mapping(benchmark_mapping_path)
    snapshot = build_realtime_snapshot(watchlist_path, benchmark_mapping_path, ts)
    meta_by_code = {meta.code: meta for meta in watchlist}
    realtime_by_code = {item["code"]: item for item in snapshot["items"]}
    list_items = [
        {
            "code": item["code"],
            "name": item["name"],
            "type": item["type"],
            "price": item["price"],
            "iopv": item["iopv"],
            "premium": item["premium"],
            "coverage": item["coverage"],
            "pctile_30d": item["pctile_30d"],
            "source_quality": item["source_quality"],
        }
        for item in snapshot["items"]
    ]
    list_items.sort(key=lambda item: item["premium"], reverse=True)

    first_code = watchlist[0].code
    detail = _build_detail(meta_by_code[first_code], realtime_by_code[first_code], benchmark_mapping.get(first_code, []), ts)
    history = _build_history(first_code, ts)

    return {
        "list": _ok({"ts": ts, "items": list_items}),
        "detail": _ok(detail),
        "history": _ok({"code": first_code, "granularity": "day", "items": history}),
        "ingest": _ok({"accepted": len(snapshot["items"]), "rejected": 0}),
    }


def write_sample_outputs(output_dir: str | Path, ts: str = DEFAULT_TS) -> dict[str, Path]:
    import json

    watchlist_path, benchmark_mapping_path = default_asset_paths()
    samples = build_sample_api_outputs(watchlist_path, benchmark_mapping_path, ts)
    snapshot = build_realtime_snapshot(watchlist_path, benchmark_mapping_path, ts)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    files = {
        "snapshot": output_path / "backend-realtime-snapshot-v2.json",
        "list": output_path / "backend-sample-api-lof-list-v2.json",
        "detail": output_path / "backend-sample-api-lof-detail-v2.json",
        "history": output_path / "backend-sample-api-lof-history-v2.json",
        "ingest": output_path / "backend-sample-ingest-realtime-v2.json",
    }
    payloads = {
        "snapshot": snapshot,
        "list": samples["list"],
        "detail": samples["detail"],
        "history": samples["history"],
        "ingest": {"ts": snapshot["ts"], "items": [_ingest_item(item) for item in snapshot["items"]]},
    }
    for key, file_path in files.items():
        file_path.write_text(json.dumps(payloads[key], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return files


def _build_detail(meta: Any, realtime: dict[str, Any], components: list[BenchmarkComponent], ts: str) -> dict[str, Any]:
    return {
        "code": meta.code,
        "name": meta.name,
        "type": meta.type,
        "scale_yi": meta.scale_yi,
        "coverage_top10": realtime["coverage_breakdown"]["top10_weight"],
        "coverage_breakdown": realtime["coverage_breakdown"],
        "benchmark_raw": meta.benchmark_raw,
        "benchmark_components": [
            {"index_code": component.index_code, "name": component.component_name, "weight": component.weight}
            for component in components
        ],
        "holdings_top10": [],
        "realtime": {
            "ts": ts,
            "price": realtime["price"],
            "iopv": realtime["iopv"],
            "premium": realtime["premium"],
            "coverage": realtime["coverage"],
            "source_quality": realtime["source_quality"],
        },
        "pctile_30d": realtime["pctile_30d"],
    }


def _build_history(code: str, ts: str) -> list[dict[str, Any]]:
    base_date = datetime.fromisoformat(ts).date() if "T" in ts else date.fromisoformat(ts)
    items: list[dict[str, Any]] = []
    trading_day = base_date
    while len(items) < 30:
        if trading_day.weekday() < 5:
            offset = len(items)
            official_nav = round(0.95 + offset * 0.003, 4)
            premium_close = round(-0.025 + offset * 0.0018, 6)
            items.append(
                {
                    "date": trading_day.isoformat(),
                    "close_price": round(official_nav * (1 + premium_close), 4),
                    "official_nav": official_nav,
                    "premium_close": premium_close,
                    "premium_pctile_30d": round((offset + 1) / 30, 6),
                }
            )
        trading_day -= timedelta(days=1)
    return list(reversed(items))


def _ingest_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": item["code"],
        "price": item["price"],
        "iopv": item["iopv"],
        "premium": item["premium"],
        "coverage": item["coverage"],
        "source_quality": item["source_quality"],
    }


def _ok(data: dict[str, Any]) -> dict[str, Any]:
    return {"code": 0, "message": "ok", "data": data}


def _synthetic_top10_weight(fund_type: str, assigned_weight: float, index: int) -> float:
    if fund_type == "index":
        return round(min(0.65, max(0.35, assigned_weight * 0.5)), 6)
    return round(0.32 + (index % 6) * 0.035, 6)


def _synthetic_iopv(index: int) -> float:
    return round(0.85 + (index % 12) * 0.037, 4)


def _synthetic_premium_seed(index: int) -> float:
    return round(-0.018 + (index % 10) * 0.006, 6)


def _synthetic_pctile(index: int) -> float:
    return round(0.05 + (index % 20) * 0.045, 6)
