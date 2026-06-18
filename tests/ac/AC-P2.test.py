"""AC-P2: watchlist-v2 / benchmark-v2 coverage acceptance test.

Method: read watchlist-v2 and benchmark-mapping-v2, aggregate benchmark weights
by LOF code as a static coverage proxy, then verify 30 funds are covered and the
399987 numeric-code conflict is resolved.
Pass criteria: average coverage >= 0.90, count of coverage < 0.70 <= 3,
index/industry funds have coverage 1.00, benchmark weight failures = 0, and
numeric-code conflicts = 0.
Dependencies: dev-002 (watchlist-v2 / benchmark-v2), dev-004 (coverage policy).
Current status: implemented as v2 static asset acceptance.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import pytest

from _lib import AC

META = AC.P2
EXPECTED_TOTAL = 30
MIN_AVG_COVERAGE = 0.90
LOW_COVERAGE_THRESHOLD = 0.70
MAX_LOW_COVERAGE_COUNT = 3
FULL_COVERAGE_TYPES = {"\u6307\u6570", "\u884c\u4e1a"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def aggregate_weights(rows: list[dict[str, str]]) -> dict[str, float]:
    weights: dict[str, float] = defaultdict(float)
    for row in rows:
        weights[row["code"]] += float(row["weight"])
    return dict(weights)


def detect_numeric_index_conflicts(rows: list[dict[str, str]]) -> dict[str, set[tuple[str, str]]]:
    by_numeric_code: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in rows:
        index_code = row["index_code"]
        if index_code == "CASH":
            continue
        numeric_code = index_code.split(".", 1)[0]
        by_numeric_code[numeric_code].add((index_code, row["component_name"]))
    return {
        numeric_code: mappings
        for numeric_code, mappings in by_numeric_code.items()
        if len(mappings) > 1
    }


@pytest.mark.ac_p
def test_ac_p2_watchlist_v2_benchmark_coverage(project_root):
    """AC-P2: all 30 watchlist-v2 funds must be fully covered by benchmark-v2."""
    assert META.code == "AC-P2"
    watchlist = read_csv(project_root / "assets" / "lof-watchlist-v2.csv")
    benchmark_rows = read_csv(project_root / "assets" / "benchmark-mapping-v2.csv")
    watch_codes = {row["code"] for row in watchlist}
    coverage_by_code = aggregate_weights(benchmark_rows)

    assert len(watchlist) == EXPECTED_TOTAL
    assert len(watch_codes) == EXPECTED_TOTAL, "watchlist-v2 code must be unique"
    assert set(coverage_by_code) == watch_codes

    coverage_values = list(coverage_by_code.values())
    average_coverage = sum(coverage_values) / len(coverage_values)
    low_coverage_codes = [
        code for code, coverage in coverage_by_code.items()
        if coverage < LOW_COVERAGE_THRESHOLD
    ]

    assert average_coverage >= MIN_AVG_COVERAGE
    assert len(low_coverage_codes) <= MAX_LOW_COVERAGE_COUNT

    for code, coverage in coverage_by_code.items():
        assert abs(coverage - 1.0) <= 1e-9, f"{code} benchmark weight sum is {coverage}"

    for row in watchlist:
        if row["type"] in FULL_COVERAGE_TYPES:
            assert coverage_by_code[row["code"]] == 1.0

    conflicts = detect_numeric_index_conflicts(benchmark_rows)
    assert conflicts == {}

    conflict_399987_rows = [
        row for row in benchmark_rows
        if row["index_code"].split(".", 1)[0] == "399987"
    ]
    assert len(conflict_399987_rows) == 1
    assert conflict_399987_rows[0]["code"] == "160632"
    assert conflict_399987_rows[0]["index_code"] == "399987.SZ"
