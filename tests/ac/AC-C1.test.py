"""AC-C1: collection continuity local sample smoke.

Method: use dev-004 realtime snapshot sample as a single-minute M1 smoke proxy
for the fetcher -> ingest payload. Full trading-day replay still waits for a
real one-day collection log.
Pass criteria for current M1 smoke: one timestamp contains exactly 30 unique LOF
rows and no stale rows. Full AC remains to be extended with real day replay.
Dependency: dev-004 sample-output.
Current status: implemented as local one-minute smoke; full-day replay pending.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.m1_backend import build_realtime_snapshot

META = AC.C1


@pytest.mark.ac_c
def test_ac_c1_realtime_snapshot_has_one_complete_30_row_minute(project_root):
    assert META.code == "AC-C1"
    snapshot = build_realtime_snapshot(project_root)
    items = snapshot["items"]

    assert len(items) == 30
    assert len({item["code"] for item in items}) == 30
    assert all(item["source_quality"] in {"ok", "degraded"} for item in items)
    assert all(0 <= item["coverage"] <= 1 for item in items)
