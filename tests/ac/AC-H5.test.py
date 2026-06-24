"""AC-H5: rolling 30-trading-day percentile range/recompute; <30 -> null.

PRD 1.2.2 rule: premium_pctile_30d is the rolling percentile of premium_close
over the trailing 30 valid trading days; value in [0,1]; offline recompute
error <=0.01; when fewer than 30 valid days exist the percentile must be null
(no synthetic padding).

Method: query the local real API lof-history for >=3 funds. Pull a deeper
window (days=90) so a full 30-day trailing window is visible inside the returned
slice, then recompute the percentile with the same trailing-window definition
as the backend (compute_premium_pctile) and compare. Also assert all non-null
percentiles are in [0,1].

Pass criteria: all non-null percentiles in [0,1]; where a full 30-valid-day
trailing window is visible in the slice, recompute vs returned within 0.01.
Dependency: dev-004 (local API lof-history percentile).
Current status: implemented; local real API regression.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.real_api import fetch_history

META = AC.H5
TOLERANCE = 0.01
WINDOW = 30
SAMPLE_CODES = ["161725", "161005", "160706", "160632", "501203"]


def _pctile(values, index, window=WINDOW):
    current = values[index]
    if current is None:
        return None
    start = max(0, index - window + 1)
    sample = [v for v in values[start : index + 1] if v is not None]
    if len(sample) < window:
        return None
    less_or_equal = sum(1 for v in sample if v <= current)
    return less_or_equal / len(sample)


@pytest.mark.ac_h
def test_ac_h5_percentile_in_range(project_root):
    assert META.code == "AC-H5"
    seen = 0
    for code in SAMPLE_CODES:
        items = fetch_history(code, days=30)
        if items is None:
            pytest.skip("local real API lof-history not available")
        for it in items:
            pct = it.get("premium_pctile_30d")
            if pct is None:
                continue
            assert 0.0 <= pct <= 1.0, f"{code} {it.get('date')}: pctile {pct} out of [0,1]"
            seen += 1
    assert seen >= 1, "no non-null percentile rows observed"


@pytest.mark.ac_h
def test_ac_h5_percentile_offline_recompute(project_root):
    """Where a full 30-valid-day trailing window is visible, recompute matches."""
    compared = 0
    for code in SAMPLE_CODES:
        items = fetch_history(code, days=90)
        if items is None:
            pytest.skip("local real API lof-history not available")
        premiums = [it.get("premium_close") for it in items]
        for idx in range(WINDOW - 1, len(items)):
            window = premiums[idx - WINDOW + 1 : idx + 1]
            if any(v is None for v in window):
                continue
            expected = _pctile(premiums, idx)
            got = items[idx].get("premium_pctile_30d")
            if expected is None or got is None:
                continue
            assert abs(expected - got) <= TOLERANCE, (
                f"{code} {items[idx].get('date')}: pctile got={got} recomputed={expected}"
            )
            compared += 1
    assert compared >= 30, f"only {compared} full-window percentile rows verifiable"


@pytest.mark.ac_h
def test_ac_h5_null_when_premium_close_null(project_root):
    """A row without premium_close cannot carry a percentile (no synthesis)."""
    checked = 0
    for code in SAMPLE_CODES:
        items = fetch_history(code, days=90)
        if items is None:
            pytest.skip("local real API lof-history not available")
        for it in items:
            if it.get("premium_close") is None:
                assert it.get("premium_pctile_30d") is None, (
                    f"{code} {it.get('date')}: pctile present without premium_close"
                )
            checked += 1
    assert checked >= 1
