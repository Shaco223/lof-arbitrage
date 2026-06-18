from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = ROOT / "tests"
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))
from contract.prd6_contracts import (
    API_LOF_DETAIL_DATA,
    API_LOF_HISTORY_DATA,
    API_LOF_LIST_DATA,
    API_LOF_LIST_ITEM,
    COMMON_RESPONSE,
    COVERAGE_BREAKDOWN,
    HISTORY_ITEM,
    INGEST_REALTIME_ITEM,
    REALTIME_BLOCK,
    assert_contract,
)
from fetcher.pipeline.snapshot import build_realtime_snapshot, build_sample_api_outputs


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_generated_samples_match_prd6_contracts():
    sample = build_sample_api_outputs(
        PROJECT_ROOT / "assets" / "lof-watchlist-v2.csv",
        PROJECT_ROOT / "assets" / "benchmark-mapping-v2.csv",
    )

    assert_contract("list.response", sample["list"], COMMON_RESPONSE)
    assert_contract("list.data", sample["list"]["data"], API_LOF_LIST_DATA)
    for item in sample["list"]["data"]["items"]:
        assert_contract("list.item", item, API_LOF_LIST_ITEM)

    assert_contract("detail.response", sample["detail"], COMMON_RESPONSE)
    assert_contract("detail.data", sample["detail"]["data"], API_LOF_DETAIL_DATA)
    assert_contract("detail.coverage_breakdown", sample["detail"]["data"]["coverage_breakdown"], COVERAGE_BREAKDOWN)
    assert_contract("detail.realtime", sample["detail"]["data"]["realtime"], REALTIME_BLOCK)

    assert_contract("history.response", sample["history"], COMMON_RESPONSE)
    assert_contract("history.data", sample["history"]["data"], API_LOF_HISTORY_DATA)
    for item in sample["history"]["data"]["items"]:
        assert_contract("history.item", item, HISTORY_ITEM)


def test_generated_ingest_snapshot_matches_prd6_item_contract():
    snapshot = build_realtime_snapshot(
        PROJECT_ROOT / "assets" / "lof-watchlist-v2.csv",
        PROJECT_ROOT / "assets" / "benchmark-mapping-v2.csv",
    )

    assert len(snapshot["items"]) == 30
    for item in snapshot["items"]:
        ingest_item = {key: item[key] for key in ["code", "price", "iopv", "premium", "coverage", "source_quality"]}
        assert_contract("ingest.item", ingest_item, INGEST_REALTIME_ITEM)
