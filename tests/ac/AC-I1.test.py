"""AC-I1: api-lof-list local M1 smoke acceptance.

Method: build dev-004 sample API outputs from watchlist-v2 / benchmark-v2 and
validate the list response. The local Python fetcher sample-output still emits
PRD 1.1 fields, so this offline smoke validates the 1.1 legacy subset; the full
PRD 1.2 contract is enforced by the real local API e2e suite
(tests/e2e/test_real_api_acceptance.py).
Pass criteria: p95 <= 800 ms, 30 rows returned, and every list item carries the
nine PRD 1.1 legacy fields with correct types/enums.
Dependency: dev-004 local backend sample-output / uniCloud list function.
Current status: implemented as local 1.1 smoke; full 1.2 regression runs on the
real local API.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.m1_backend import build_sample_api_outputs, measure_call_ms
from contract.prd6_contracts import (
    API_LOF_LIST_DATA,
    API_LOF_LIST_ITEM_LEGACY,
    COMMON_RESPONSE,
    assert_contract,
)

META = AC.I1


@pytest.mark.ac_i
def test_ac_i1_list_sample_output_matches_prd6_contract(project_root):
    assert META.code == "AC-I1"
    samples = build_sample_api_outputs(project_root)
    response = samples["list"]

    assert_contract("api-lof-list.response", response, COMMON_RESPONSE)
    assert_contract("api-lof-list.data", response["data"], API_LOF_LIST_DATA)
    assert len(response["data"]["items"]) == 30
    for item in response["data"]["items"]:
        assert_contract("api-lof-list.data.items[]", item, API_LOF_LIST_ITEM_LEGACY)


@pytest.mark.ac_i
def test_ac_i1_local_sample_builder_p95_under_800ms(project_root):
    p95 = measure_call_ms(lambda: build_sample_api_outputs(project_root), repeat=20)
    assert p95 <= 800
