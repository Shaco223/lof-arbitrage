"""AC-H6: premium_estimate_close = close-time price/IOPV - 1, no synthesis.

PRD 1.2.3 rule: premium_estimate_close is the close-time real price/IOPV - 1.
It must NOT be synthesized by buildFallbackHistory. Before the enable date
(2026-06-22) it is null; from the enable date onward it appears per trading day
once real close-time IOPV is captured.

Method: query local real API lof-history for >=3 funds. Assert all rows dated
before 2026-06-22 have premium_estimate_close == null. For rows on/after the
enable date, when a value is present it must be consistent (a finite number);
the current local sample link has not captured real close-time IOPV yet, so
null on/after the enable date is acceptable (no synthesis), but a non-null
value before the enable date is a hard failure.

Pass criteria: no premium_estimate_close before 2026-06-22; any present value
is a finite number; field never fabricated by fallback.
Dependency: dev-004 (real close-time IOPV backfill).
Current status: implemented; local real API regression (pre-enable guard).
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.real_api import fetch_history

META = AC.H6
ENABLE_DATE = "2026-06-22"
SAMPLE_CODES = ["161725", "161005", "160706", "160632", "501203"]


@pytest.mark.ac_h
def test_ac_h6_estimate_close_null_before_enable(project_root):
    assert META.code == "AC-H6"
    rows_seen = 0
    for code in SAMPLE_CODES:
        items = fetch_history(code, days=30)
        if items is None:
            pytest.skip("local real API lof-history not available")
        for it in items:
            rows_seen += 1
            est = it.get("premium_estimate_close")
            if it.get("date", "") < ENABLE_DATE:
                assert est is None, f"{code} {it.get('date')}: estimate before enable must be null, got {est}"
            elif est is not None:
                assert isinstance(est, (int, float)) and not isinstance(est, bool), (
                    f"{code} {it.get('date')}: estimate must be number, got {est!r}"
                )
    assert rows_seen >= 1
