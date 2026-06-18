from __future__ import annotations

from pathlib import Path

from fetcher.pipeline.snapshot import build_realtime_snapshot, build_sample_api_outputs, default_asset_paths


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_default_asset_paths_point_to_v2_files():
    watchlist_path, benchmark_path = default_asset_paths(PROJECT_ROOT / "lof-fetcher")

    assert watchlist_path == PROJECT_ROOT / "assets" / "lof-watchlist-v2.csv"
    assert benchmark_path == PROJECT_ROOT / "assets" / "benchmark-mapping-v2.csv"


def test_build_realtime_snapshot_uses_v2_assets_for_30_lofs():
    snapshot = build_realtime_snapshot(
        watchlist_path=PROJECT_ROOT / "assets" / "lof-watchlist-v2.csv",
        benchmark_mapping_path=PROJECT_ROOT / "assets" / "benchmark-mapping-v2.csv",
        ts="2026-06-18T10:31:00+08:00",
    )

    assert snapshot["ts"] == "2026-06-18T10:31:00+08:00"
    assert len(snapshot["items"]) == 30
    assert {item["code"] for item in snapshot["items"]} == {
        row.split(",", 1)[0]
        for row in (PROJECT_ROOT / "assets" / "lof-watchlist-v2.csv").read_text(encoding="utf-8-sig").splitlines()[1:]
        if row.strip()
    }
    assert all(0 <= item["coverage"] <= 1 for item in snapshot["items"])
    assert all(item["source_quality"] in {"ok", "degraded", "stale"} for item in snapshot["items"])


def test_build_sample_api_outputs_match_prd6_shapes():
    sample = build_sample_api_outputs(
        watchlist_path=PROJECT_ROOT / "assets" / "lof-watchlist-v2.csv",
        benchmark_mapping_path=PROJECT_ROOT / "assets" / "benchmark-mapping-v2.csv",
        ts="2026-06-18T10:31:00+08:00",
    )

    assert sample["list"]["code"] == 0
    assert len(sample["list"]["data"]["items"]) == 30
    detail = sample["detail"]["data"]
    assert detail["coverage_breakdown"] == {
        "top10_weight": detail["coverage_top10"],
        "benchmark_assigned_weight": 0.95,
        "cash_weight": 0.05,
    }
    assert len(sample["history"]["data"]["items"]) == 30
    assert sample["ingest"]["data"] == {"accepted": 30, "rejected": 0}
