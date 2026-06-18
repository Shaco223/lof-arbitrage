"""PRD §6.2 api-lof-detail static contract."""
from __future__ import annotations

import pytest

from contract.prd6_contracts import (
    API_LOF_DETAIL_DATA,
    API_LOF_DETAIL_REQUIRED_BLOCKS,
    API_LOF_DETAIL_SAMPLE,
    BENCHMARK_COMPONENT,
    COMMON_RESPONSE,
    COVERAGE_BREAKDOWN,
    HOLDING_TOP10_ITEM,
    REALTIME_BLOCK,
    assert_contract,
)


@pytest.mark.contract
def test_api_lof_detail_response_contains_six_required_prd9_blocks():
    response = API_LOF_DETAIL_SAMPLE
    assert_contract("api-lof-detail.response", response, COMMON_RESPONSE)
    assert_contract("api-lof-detail.data", response["data"], API_LOF_DETAIL_DATA)
    assert API_LOF_DETAIL_REQUIRED_BLOCKS <= set(response["data"])


@pytest.mark.contract
def test_api_lof_detail_nested_blocks_match_prd6_contract():
    data = API_LOF_DETAIL_SAMPLE["data"]
    assert_contract("api-lof-detail.coverage_breakdown", data["coverage_breakdown"], COVERAGE_BREAKDOWN)
    assert data["benchmark_components"], "benchmark_components should include at least one component"
    for item in data["benchmark_components"]:
        assert_contract("api-lof-detail.benchmark_components[]", item, BENCHMARK_COMPONENT)
    assert data["holdings_top10"], "holdings_top10 should include at least one holding"
    for item in data["holdings_top10"]:
        assert_contract("api-lof-detail.holdings_top10[]", item, HOLDING_TOP10_ITEM)
    assert_contract("api-lof-detail.realtime", data["realtime"], REALTIME_BLOCK)
