"""AC-P7: subscribe limit amount parsed independently; only limited+number.

PRD 1.3 rule: subscribe_limit_amount (yuan, nullable) parsed independently of
status; only when subscribe_status == limited AND the source text carries a
number is the amount parsed, with subscribe_limit_period = "day". Open / no
number / no source / sentinel MAXSG=1000亿 (1e11) -> null.

Sample checks: 161725=500000, 161005=20000, 160632=200000, 160706=null (open),
501203=null (limited but no number in text). 501050/501090 open -> null.

Method: query local real API lof-list and verify the sampled amounts, the
independence rule (amount null unless limited), and the period rule (period
present only when amount present).

Pass criteria: sampled amounts match; non-limited rows have null amount; period
== "day" iff amount present; no sentinel 1e11 leaks through.
Dependency: dev-004 (local API lof-list limit parsing).
Current status: implemented; local real API regression.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.real_api import fetch_list_items

META = AC.P7
SENTINEL = 1e11
EXPECTED = {
    "161725": 500000,
    "161005": 20000,
    "160632": 200000,
    "160706": None,
    "501203": None,
    "501050": None,
    "501090": None,
}


@pytest.mark.ac_p
def test_ac_p7_limit_amount_sampling(project_root):
    assert META.code == "AC-P7"
    items = fetch_list_items()
    if items is None:
        pytest.skip("local real API lof-list not available")
    by_code = {it.get("code"): it for it in items}
    for code, expected_amount in EXPECTED.items():
        item = by_code.get(code)
        assert item is not None, f"{code} missing from list"
        amount = item.get("subscribe_limit_amount")
        if expected_amount is None:
            assert amount is None, f"{code}: expected null amount, got {amount}"
        else:
            assert amount is not None and abs(amount - expected_amount) < 1.0, (
                f"{code}: expected {expected_amount}, got {amount}"
            )


@pytest.mark.ac_p
def test_ac_p7_amount_independence_and_period(project_root):
    items = fetch_list_items()
    if items is None:
        pytest.skip("local real API lof-list not available")
    for item in items:
        sub = item.get("subscribe_status")
        amount = item.get("subscribe_limit_amount")
        period = item.get("subscribe_limit_period")
        if amount is not None:
            assert sub == "limited", f"{item.get('code')}: amount set but status={sub}"
            assert amount != SENTINEL, f"{item.get('code')}: sentinel 1e11 leaked as amount"
            assert period == "day", f"{item.get('code')}: amount set but period={period}"
        else:
            assert period is None, f"{item.get('code')}: amount null but period={period}"
