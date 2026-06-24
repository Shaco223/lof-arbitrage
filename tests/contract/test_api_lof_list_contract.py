"""PRD 6.1 api-lof-list static contract (PRD 1.2)."""
from __future__ import annotations

import pytest

from contract.prd6_contracts import (
    API_LOF_LIST_DATA,
    API_LOF_LIST_ITEM,
    API_LOF_LIST_ITEM_LEGACY_REQUIRED,
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
def test_api_lof_list_item_contract_has_prd_1_2_fields():
    # PRD 1.3: list items[] expose 22 fields; 9 legacy fields stay required.
    assert set(API_LOF_LIST_ITEM) == {
        "code",
        "name",
        "type",
        "status",
        "price",
        "price_change_pct",
        "volume_amount",
        "iopv",
        "premium",
        "nav_official",
        "nav_official_date",
        "premium_nav",
        "premium_error",
        "coverage",
        "pctile_30d",
        "source_quality",
        "subscribe_status",
        "redeem_status",
        "fund_scale",
        "circulating_shares",
        "subscribe_limit_amount",
        "subscribe_limit_period",
    }
    assert len(API_LOF_LIST_ITEM) == 22


@pytest.mark.contract
def test_api_lof_list_item_keeps_legacy_required_fields():
    # Legacy 1.1 fields must remain present and required (no rename/removal).
    for key in API_LOF_LIST_ITEM_LEGACY_REQUIRED:
        assert key in API_LOF_LIST_ITEM, f"legacy field {key} missing"
        assert API_LOF_LIST_ITEM[key].required, f"legacy field {key} must stay required"
