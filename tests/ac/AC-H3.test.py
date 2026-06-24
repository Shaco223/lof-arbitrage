"""AC-H3: history real daily close/nav, not buildFallbackHistory synthesis.

PRD 1.2.2 rule: lof-history must return real daily close_price / official_nav
per trading day, never the synthetic buildFallbackHistory series
(baseDate=2026-06-18, close=0.9262+offset*0.0047, nav=0.95+offset*0.003).

Method: query the local real API lof-history for >=3 funds and assert the rows
do NOT match the synthetic fallback signature: distinct close series across
codes, and newest close != 0.9262 fallback seed. When the local API is not
available the test skips (real backend required).

Pass criteria: each fund returns >=20 rows; close series differ across funds;
no fund matches the buildFallbackHistory close formula.
Dependency: dev-004 (local API lof-history real daily backfill).
Current status: implemented; local real API regression.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.real_api import fetch_history

META = AC.H3
SAMPLE_CODES = ["161725", "161005", "160706", "160632", "501203"]
FALLBACK_SEED = 0.9262
FALLBACK_STEP = 0.0047


def _matches_fallback(items):
    closes = [it.get("close_price") for it in items]
    if not closes or closes[0] is None:
        return False
    # fallback newest (index 0 ascending->reversed) seed check
    expected = [round(FALLBACK_SEED + i * FALLBACK_STEP, 6) for i in range(len(closes))]
    return all(c is not None and abs(c - e) <= 1e-6 for c, e in zip(closes, expected))


@pytest.mark.ac_h
def test_ac_h3_history_is_real_not_synthetic(project_root):
    assert META.code == "AC-H3"
    series = {}
    for code in SAMPLE_CODES:
        items = fetch_history(code, days=30)
        if items is None:
            pytest.skip("local real API lof-history not available")
        assert len(items) >= 20, f"{code}: expected >=20 rows, got {len(items)}"
        assert not _matches_fallback(items), f"{code}: history matches synthetic fallback"
        series[code] = tuple(it.get("close_price") for it in items)
    # Real per-fund data must differ across codes (synthesis would be identical).
    assert len({s for s in series.values()}) == len(series), "history close series identical across funds"
