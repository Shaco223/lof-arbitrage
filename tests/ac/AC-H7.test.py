"""AC-H7: premium_deviation = premium_estimate_close - premium_close.

PRD 1.2.3 rule: premium_deviation == premium_estimate_close - premium_close,
offline recompute error <=1e-4. If either operand is null, premium_deviation
must be null (never 0).

Method: query local real API lof-history for >=3 funds and validate the
relationship row-by-row.

Pass criteria: when both operands present, abs(deviation - (est - close)) <=
1e-4; when either operand null, deviation is null.
Dependency: dev-004 (real close-time IOPV backfill).
Current status: implemented; local real API regression.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.real_api import fetch_history

META = AC.H7
TOLERANCE = 1e-4
SAMPLE_CODES = ["161725", "161005", "160706", "160632", "501203"]


@pytest.mark.ac_h
def test_ac_h7_deviation_relationship(project_root):
    assert META.code == "AC-H7"
    rows_seen = 0
    for code in SAMPLE_CODES:
        items = fetch_history(code, days=30)
        if items is None:
            pytest.skip("local real API lof-history not available")
        for it in items:
            rows_seen += 1
            est = it.get("premium_estimate_close")
            close = it.get("premium_close")
            dev = it.get("premium_deviation")
            if est is None or close is None:
                assert dev is None, f"{code} {it.get('date')}: deviation must be null when operand null, got {dev}"
                continue
            assert dev is not None, f"{code} {it.get('date')}: deviation should not be null when operands present"
            assert abs(dev - (est - close)) <= TOLERANCE, (
                f"{code} {it.get('date')}: deviation={dev} est-close={est - close}"
            )
    assert rows_seen >= 1
