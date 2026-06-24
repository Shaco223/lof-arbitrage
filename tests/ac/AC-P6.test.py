"""AC-P6: subscribe/redeem status enums restricted; unknown fallback safe.

PRD 1.3 rule: subscribe_status enum = {open, limited, suspended, closed,
unknown} (5 values); redeem_status enum = {open, suspended, closed, unknown}
(4 values, no limited). Primary source fundmob_basic, fallback HTML, default
unknown when source down; unknown must not raise.

Method: query local real API lof-list (30 rows) and assert every
subscribe_status / redeem_status is within the restricted enum and contract
validation passes. Static guard: the contract enum already encodes the
restriction; this test enforces it against real data and that the field may be
"unknown" without error.

Pass criteria: all 30 rows pass contract; subscribe_status in 5-value enum,
redeem_status in 4-value enum (never "limited").
Dependency: dev-004 (local API lof-list status fields).
Current status: implemented; local real API regression + contract guard.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.real_api import fetch_list_items
from contract.prd6_contracts import (
    API_LOF_LIST_ITEM,
    REDEEM_STATUS,
    SUBSCRIBE_STATUS,
    assert_contract,
)

META = AC.P6


@pytest.mark.ac_p
def test_ac_p6_status_enums_restricted(project_root):
    assert META.code == "AC-P6"
    items = fetch_list_items()
    if items is None:
        pytest.skip("local real API lof-list not available")
    assert len(items) == 30, f"expected 30 rows, got {len(items)}"
    for item in items:
        assert_contract("api-lof-list.data.items[]", item, API_LOF_LIST_ITEM)
        sub = item.get("subscribe_status")
        red = item.get("redeem_status")
        assert sub is None or sub in SUBSCRIBE_STATUS, f"{item.get('code')}: bad subscribe_status {sub}"
        assert red is None or red in REDEEM_STATUS, f"{item.get('code')}: bad redeem_status {red}"
        assert red != "limited", f"{item.get('code')}: redeem_status must not be 'limited'"


@pytest.mark.ac_p
def test_ac_p6_unknown_status_passes_contract(project_root):
    """Source-down sentinel: unknown must validate without raising."""
    item = {
        "code": "000000",
        "name": "x",
        "type": "index",
        "status": "active",
        "price": None,
        "price_change_pct": None,
        "volume_amount": None,
        "iopv": None,
        "premium": None,
        "nav_official": None,
        "nav_official_date": None,
        "premium_nav": None,
        "premium_error": None,
        "coverage": None,
        "pctile_30d": None,
        "source_quality": "stale",
        "subscribe_status": "unknown",
        "redeem_status": "unknown",
    }
    assert_contract("api-lof-list.data.items[] (unknown)", item, API_LOF_LIST_ITEM)
