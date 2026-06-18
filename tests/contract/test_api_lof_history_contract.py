"""PRD §6.3 api-lof-history static contract."""
from __future__ import annotations

import pytest

from contract.prd6_contracts import (
    API_LOF_HISTORY_DATA,
    API_LOF_HISTORY_SAMPLE,
    COMMON_RESPONSE,
    HISTORY_ITEM,
    assert_contract,
)


@pytest.mark.contract
def test_api_lof_history_response_matches_prd6_contract():
    response = API_LOF_HISTORY_SAMPLE
    assert_contract("api-lof-history.response", response, COMMON_RESPONSE)
    assert_contract("api-lof-history.data", response["data"], API_LOF_HISTORY_DATA)
    assert response["data"]["items"], "api-lof-history.data.items should include history rows"
    for item in response["data"]["items"]:
        assert_contract("api-lof-history.data.items[]", item, HISTORY_ITEM)


@pytest.mark.contract
def test_api_lof_history_pctile_field_uses_prd5_history_name():
    assert "premium_pctile_30d" in HISTORY_ITEM
    assert "pctile_30d" not in HISTORY_ITEM
