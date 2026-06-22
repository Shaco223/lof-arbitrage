"""AC-P4: nav-based premium formula acceptance.

PRD 1.2 rule: premium_nav = (price - nav_official) / nav_official.

Method: query the local real API lof-list (>=30 rows) and recompute premium_nav
row-by-row, asserting agreement within 1e-4. The backend rounds premium_nav to
6 decimals (round6), so a 1e-4 tolerance is comfortable. When the local API is
not running, fall back to the dev-004 PRD 1.2 field sample
(outputs/backend-prd1.2-field-sample-v2.json) so the formula is still verified
offline; if neither source is available the test skips.

Pass criteria: every row with price and nav_official > 0 satisfies
abs((price - nav_official)/nav_official - premium_nav) <= 1e-4.
Dependency: dev-004 (local API lof-list / sample output).
Current status: implemented; local real API regression preferred, sample
fallback otherwise.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from _lib import AC

META = AC.P4
TOLERANCE = 1e-4
DEFAULT_LOCAL_API_BASE = "http://127.0.0.1:8787"
REAL_API_BASE = os.getenv("REAL_API_BASE", DEFAULT_LOCAL_API_BASE).rstrip("/")
FN_LIST = os.getenv("REAL_API_FN_LIST", "lof-list")


def _fetch_local_list_items():
    if "next.bspapp.com" in REAL_API_BASE and os.getenv("ALLOW_ONLINE_REAL_API") != "1":
        return None
    url = f"{REAL_API_BASE}/{FN_LIST}?" + urllib.parse.urlencode({"sort": "code"})
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, TimeoutError, ValueError):
        return None
    return payload.get("data", {}).get("items")


def _fallback_sample_items(project_root: Path):
    sample = project_root / "outputs" / "backend-prd1.2-field-sample-v2.json"
    if not sample.exists():
        return None
    data = json.loads(sample.read_text(encoding="utf-8"))
    return data.get("list_first_three")


def _check_rows(items):
    checked = 0
    for item in items:
        price = item.get("price")
        nav_official = item.get("nav_official")
        premium_nav = item.get("premium_nav")
        if price is None or nav_official in (None, 0) or premium_nav is None:
            continue
        recomputed = (price - nav_official) / nav_official
        assert abs(recomputed - premium_nav) <= TOLERANCE, (
            f"{item.get('code')}: premium_nav={premium_nav} recomputed={recomputed}"
        )
        checked += 1
    return checked


@pytest.mark.ac_p
def test_ac_p4_premium_nav_formula_local_api(project_root):
    assert META.code == "AC-P4"
    items = _fetch_local_list_items()
    if items is None:
        pytest.skip(f"local real API not available at {REAL_API_BASE}")
    assert len(items) >= 30, f"expected >=30 list rows, got {len(items)}"
    checked = _check_rows(items)
    assert checked >= 30, f"only {checked} rows had price/nav_official/premium_nav to verify"


@pytest.mark.ac_p
def test_ac_p4_premium_nav_formula_offline_sample(project_root):
    """Offline guard: formula must hold on dev-004 PRD 1.2 field sample too."""
    items = _fallback_sample_items(project_root)
    if not items:
        pytest.skip("PRD 1.2 field sample not available")
    checked = _check_rows(items)
    assert checked >= 1, "sample had no verifiable premium_nav rows"
