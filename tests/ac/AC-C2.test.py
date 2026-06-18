"""AC-C2: data-source failure retry acceptance placeholder.

M1 backend merged source fallback documentation, but no executable retry sample
output has been provided yet. Keep this AC pending until dev-004 supplies a
failure/retry trace that proves 3 retries within 30 seconds and final log/skip
behavior.
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.C2


@pytest.mark.ac_c
@pytest.mark.pending
def test_ac_c2_retry_trace_pending_until_sample_output_available():
    assert META.code == "AC-C2"
    # Waiting for dev-004 retry sample output: source failure -> 3 retries -> log and skip.
