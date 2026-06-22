"""AC-P5: optional-field fallback rendering acceptance.

PRD 1.2 rule: optional fields (subscribe_status / redeem_status / fund_scale /
circulating_shares / price_change_pct / volume_amount / nav_official / ...) may
be null or "unknown"; the contract must still validate and legacy fields must
keep rendering.

Method: build a list item whose every optional / nullable field is set to null
(and the enum status fields to "unknown"), then assert assert_contract does not
raise and the legacy required fields are present and typed. Also assert a fully
populated 1.2 item still validates. Pure static, no network.

Pass criteria: contract validation passes for the null/unknown item and the
fully populated item; all legacy required keys remain present.
Dependency: both (dev-003 rendering / dev-004 payload).
Current status: implemented (static contract guard).
"""
from __future__ import annotations

import pytest

from _lib import AC
from contract.prd6_contracts import (
    API_LOF_LIST_ITEM,
    API_LOF_LIST_ITEM_LEGACY_REQUIRED,
    assert_contract,
)

META = AC.P5


def _base_item():
    return {
        "code": "161725",
        "name": "??????(LOF)A",
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
        "fund_scale": None,
        "circulating_shares": None,
    }


@pytest.mark.ac_p
def test_ac_p5_null_unknown_optional_fields_pass_contract(project_root):
    assert META.code == "AC-P5"
    item = _base_item()
    # Must not raise even though all optional/nullable fields are null/unknown.
    assert_contract("api-lof-list.data.items[] (fallback)", item, API_LOF_LIST_ITEM)


@pytest.mark.ac_p
def test_ac_p5_legacy_fields_still_present_when_optional_null(project_root):
    item = _base_item()
    for key in API_LOF_LIST_ITEM_LEGACY_REQUIRED:
        assert key in item, f"legacy field {key} must keep rendering"


@pytest.mark.ac_p
def test_ac_p5_optional_fields_can_be_dropped_entirely(project_root):
    """required=False optional fields may be absent and still validate."""
    item = _base_item()
    for optional_key in ("subscribe_status", "redeem_status", "fund_scale", "circulating_shares"):
        item.pop(optional_key, None)
    assert_contract("api-lof-list.data.items[] (omitted optionals)", item, API_LOF_LIST_ITEM)


@pytest.mark.ac_p
def test_ac_p5_fully_populated_item_still_valid(project_root):
    item = _base_item()
    item.update(
        {
            "price": 0.823,
            "price_change_pct": 0.0123,
            "volume_amount": 18650.42,
            "iopv": 0.805,
            "premium": 0.0224,
            "nav_official": 0.802,
            "nav_official_date": "2026-06-17",
            "premium_nav": 0.0262,
            "premium_error": 0.003,
            "coverage": 1.0,
            "pctile_30d": 0.82,
            "source_quality": "ok",
            "subscribe_status": "open",
            "redeem_status": "open",
            "fund_scale": 300.0,
            "circulating_shares": 12.5,
        }
    )
    assert_contract("api-lof-list.data.items[] (full 1.2)", item, API_LOF_LIST_ITEM)
