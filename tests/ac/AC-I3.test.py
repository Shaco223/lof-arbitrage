"""AC-I3: api-lof-history local M1 smoke acceptance.

Method: build dev-004 sample history output and validate the PRD section 6.3
response for 30-day day granularity history.
Pass criteria: at least 20 trading-day rows are returned and every row matches
history item contract.
Dependency: dev-004 local backend sample-output / uniCloud history function.
Current status: implemented as local smoke; real deployed API regression waits
for baseURL.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.m1_backend import build_sample_api_outputs
from contract.prd6_contracts import API_LOF_HISTORY_DATA, COMMON_RESPONSE, HISTORY_ITEM, assert_contract

META = AC.I3


@pytest.mark.ac_i
def test_ac_i3_history_sample_output_has_30_day_contract(project_root):
    assert META.code == "AC-I3"
    response = build_sample_api_outputs(project_root)["history"]
    data = response["data"]

    assert_contract("api-lof-history.response", response, COMMON_RESPONSE)
    assert_contract("api-lof-history.data", data, API_LOF_HISTORY_DATA)
    assert data["granularity"] == "day"
    assert len(data["items"]) >= 20
    for item in data["items"]:
        assert_contract("api-lof-history.items[]", item, HISTORY_ITEM)
