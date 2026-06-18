"""AC-S1: uniCloud quota acceptance placeholder.

AC-S1 is a hard release gate that requires three real trading days of uniCloud
function/database usage statistics. M1 local smoke does not call paid cloud
resources, so this AC stays pending until quota export or local counting policy
is provided by dev-004/dev-001.
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.S1


@pytest.mark.ac_s
@pytest.mark.ac_hard
@pytest.mark.pending
def test_ac_s1_quota_accounting_pending_until_three_trading_days_available():
    assert META.code == "AC-S1"
    # Waiting for quota evidence: cloud function calls, database reads, database writes for 3 trading days.
