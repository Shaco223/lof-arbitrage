"""PRD §6.1 api-lof-list static contract."""
from __future__ import annotations

import pytest

from contract.prd6_contracts import (
    API_LOF_LIST_DATA,
    API_LOF_LIST_ITEM,
    API_LOF_LIST_SAMPLE,
    COMMON_RESPONSE,
    assert_contract,
)


@pytest.mark.contract
def test_api_lof_list_response_matches_prd6_sample_contract():
    response = API_LOF_LIST_SAMPLE
    assert_contract("api-lof-list.response", response, COMMON_RESPONSE)
    assert_contract("api-lof-list.data", response["data"], API_LOF_LIST_DATA)
    assert response["data"]["items"], "api-lof-list.data.items should include list rows"
    for item in response["data"]["items"]:
        assert_contract("api-lof-list.data.items[]", item, API_LOF_LIST_ITEM)


@pytest.mark.contract
def test_api_lof_list_item_contract_has_nine_prd6_fields():
    assert set(API_LOF_LIST_ITEM) == {
        "code",
        "name",
        "type",
        "price",
        "iopv",
        "premium",
        "coverage",
        "pctile_30d",
        "source_quality",
    }
