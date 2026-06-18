"""AC-S1: uniCloud quota hard-gate placeholder with local estimate check.

AC-S1 remains a hard release gate that requires three real trading days of
uniCloud function/database usage statistics. This file now verifies that the
local estimate evidence exists and is internally within the free budget, while
keeping the release-gate AC pending until real quota exports are available.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.m1_backend import run_ac_evidence

META = AC.S1
USAGE_KEYS = {"cloud_function_calls", "database_reads", "database_writes"}


def test_ac_s1_local_quota_estimate_has_budget_accounting(project_root, tmp_path):
    assert META.code == "AC-S1"
    quota = run_ac_evidence(project_root, tmp_path)["quota"]
    usage = quota["usage"]
    budget = quota["budget"]

    assert set(usage) >= USAGE_KEYS | {"assumptions"}
    assert set(budget) >= USAGE_KEYS
    assert quota["within_budget"] is True
    for key in USAGE_KEYS:
        assert isinstance(usage[key], int)
        assert usage[key] > 0
        assert usage[key] <= budget[key]
    assert usage["assumptions"]["lof_count"] == 30
    assert usage["assumptions"]["market_minutes"] == 240


@pytest.mark.ac_s
@pytest.mark.ac_hard
@pytest.mark.pending
def test_ac_s1_hard_gate_pending_until_three_trading_days_available():
    assert META.code == "AC-S1"
    # Local estimate is available, but release approval still requires 3 real trading days of quota evidence.
