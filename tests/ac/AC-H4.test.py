"""AC-H4: premium_close = close/nav - 1 offline recompute (<=1e-4).

PRD 1.2.2 rule: premium_close = (close_price / official_nav) - 1, rounded to 6
decimals by the backend. When official_nav is missing, premium_close must be
null and is skipped.

Method: query local real API lof-history for >=3 funds (>=30 rows total) and
recompute premium_close row-by-row.

Pass criteria: every row with close_price and official_nav>0 satisfies
abs((close/nav-1) - premium_close) <= 1e-4; rows missing official_nav have
premium_close == null.
Dependency: dev-004 (local API lof-history).
Current status: implemented; local real API regression.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.real_api import fetch_history

META = AC.H4
TOLERANCE = 1e-4
SAMPLE_CODES = ["161725", "161005", "160706", "160632", "501203"]


@pytest.mark.ac_h
def test_ac_h4_premium_close_formula(project_root):
    assert META.code == "AC-H4"
    checked = 0
    for code in SAMPLE_CODES:
        items = fetch_history(code, days=30)
        if items is None:
            pytest.skip("local real API lof-history not available")
        for it in items:
            close = it.get("close_price")
            nav = it.get("official_nav")
            premium_close = it.get("premium_close")
            if nav in (None, 0):
                # AC-H4: missing official_nav -> premium_close must be null.
                assert premium_close is None, f"{code} {it.get('date')}: nav null but premium_close={premium_close}"
                continue
            if close is None or premium_close is None:
                continue
            recomputed = close / nav - 1
            assert abs(recomputed - premium_close) <= TOLERANCE, (
                f"{code} {it.get('date')}: premium_close={premium_close} recomputed={recomputed}"
            )
            checked += 1
    assert checked >= 30, f"only {checked} rows verifiable for premium_close"
