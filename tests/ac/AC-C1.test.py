"""AC-C1: collection continuity local sample smoke.

Method: use dev-004 realtime snapshot sample as a single-minute M1 smoke proxy
for the fetcher -> ingest payload. Full trading-day replay still waits for a
real one-day collection log.
Pass criteria for current M1 smoke: one timestamp contains exactly N unique LOF
rows (N = watchlist-v2 size, currently 139 after PRD 1.5 expansion) and no
stale rows. Full AC remains to be extended with real day replay.
Dependency: dev-004 sample-output.
Current status: implemented as local one-minute smoke; full-day replay pending.
"""
from __future__ import annotations

import csv

import pytest

from _lib import AC
from _lib.m1_backend import build_realtime_snapshot

META = AC.C1


def _watchlist_size(project_root) -> int:
    path = project_root / "assets" / "lof-watchlist-v2.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


@pytest.mark.ac_c
def test_ac_c1_realtime_snapshot_has_one_complete_minute(project_root):
    assert META.code == "AC-C1"
    snapshot = build_realtime_snapshot(project_root)
    items = snapshot["items"]
    expected = _watchlist_size(project_root)

    assert len(items) == expected
    assert len({item["code"] for item in items}) == expected
    assert all(item["source_quality"] in {"ok", "degraded"} for item in items)
    assert all(0 <= item["coverage"] <= 1 for item in items)