"""AC-I2: api-lof-detail local M1 smoke acceptance.

Method: build dev-004 sample detail output and validate the six required PRD 9
blocks. The dev-004 sample builder now emits the full PRD 1.2/1.3 field set, so this
offline smoke validates the complete PRD 1.2/1.3 detail contract (the same
contract the real local API e2e suite enforces).
Pass criteria: detail response contains coverage_top10, coverage_breakdown,
benchmark_components, holdings_top10, realtime, pctile_30d and nested fields
match the contract.
Dependency: dev-004 local backend sample-output / uniCloud detail function.
Current status: implemented as local full 1.2/1.3 contract smoke; the real
local API e2e suite runs the same contract against the live backend.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.m1_backend import build_sample_api_outputs
from contract.prd6_contracts import (
    API_LOF_DETAIL_DATA,
    API_LOF_DETAIL_REQUIRED_BLOCKS,
    BENCHMARK_COMPONENT,
    COMMON_RESPONSE,
    COVERAGE_BREAKDOWN,
    REALTIME_BLOCK,
    assert_contract,
)

META = AC.I2


@pytest.mark.ac_i
def test_ac_i2_detail_sample_output_contains_six_required_blocks(project_root):
    assert META.code == "AC-I2"
    response = build_sample_api_outputs(project_root)["detail"]
    data = response["data"]

    assert_contract("api-lof-detail.response", response, COMMON_RESPONSE)
    assert_contract("api-lof-detail.data", data, API_LOF_DETAIL_DATA)
    assert API_LOF_DETAIL_REQUIRED_BLOCKS <= set(data)
    assert_contract("api-lof-detail.coverage_breakdown", data["coverage_breakdown"], COVERAGE_BREAKDOWN)
    assert data["benchmark_components"]
    for component in data["benchmark_components"]:
        assert_contract("api-lof-detail.benchmark_components[]", component, BENCHMARK_COMPONENT)
    assert_contract("api-lof-detail.realtime", data["realtime"], REALTIME_BLOCK)
