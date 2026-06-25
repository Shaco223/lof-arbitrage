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
    cnt = len(snapshot["items"]); assert cnt >= 122, f"expected >=122 snapshot items, got {cnt}"
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
    cnt2 = len(sample["list"]["data"]["items"]); assert cnt2 >= 122, f"expected >=122 list items, got {cnt2}"
    detail = sample["detail"]["data"]
    cb = detail["coverage_breakdown"]
    assert "top10_weight" in cb
    assert "benchmark_assigned_weight" in cb
    assert "cash_weight" in cb
    hc = len(sample["history"]["data"]["items"])
    assert hc >= 30, f"expected >=30 history items, got {hc}"
    assert sample["ingest"]["data"]["accepted"] >= 30
    assert sample["ingest"]["data"]["rejected"] == 0
