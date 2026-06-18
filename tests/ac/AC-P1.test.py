"""AC-P1?5 ??? LOF ???? vs ?? NAV ???? <= 0.5%?

?????? dev-004 BUG-004 ???? T ??? NAV ??????
``premium_truth_close``???????????? IOPV ??
``premium_estimated``?5 ? PRD ???? LOF ????
``abs(premium_estimated - premium_truth_close) <= 0.005``?
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from _lib import AC

META = AC.P1
EXPECTED_CODES = {"161725", "160706", "501050", "160119", "160222"}
TOLERANCE = 0.005


def load_premium_module(project_root: Path):
    module_path = project_root / "lof-fetcher" / "fetcher" / "engine" / "premium.py"
    spec = importlib.util.spec_from_file_location("lof_fetcher_premium", module_path)
    assert spec and spec.loader, f"???? premium ??: {module_path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.ac_p
def test_ac_p1_index_lof_realtime_premium_matches_nav_truth(project_root, fixture_dir):
    """AC-P1??? LOF ??????? NAV ??????????? 0.5%?"""
    assert META.code == "AC-P1"
    fixture_path = fixture_dir / "realtime" / "ac-p1-index-lof-samples.json"
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    samples = payload["samples"]
    premium = load_premium_module(project_root)

    assert {sample["code"] for sample in samples} == EXPECTED_CODES
    assert payload.get("tolerance", TOLERANCE) == TOLERANCE

    checked = []
    for sample in samples:
        assert sample["type"] == "index"
        official_nav = sample["official_nav_close"]
        close_price = sample["close_price"]
        expected_truth = premium.calculate_premium(price=close_price, iopv=official_nav)
        assert sample["minutes"], f"{sample['code']} ??????"

        for minute in sample["minutes"]:
            if minute.get("source_quality") == "stale" or not minute.get("iopv_estimated"):
                continue
            truth = minute["premium_truth_close"]
            estimated = minute["premium_estimated"]
            recalculated_estimated = premium.calculate_premium(
                price=minute["lof_price"],
                iopv=minute["iopv_estimated"],
            )
            assert truth == expected_truth
            assert estimated == recalculated_estimated
            error = abs(estimated - truth)
            assert error <= TOLERANCE, (
                f"{sample['code']} {minute['ts']} premium error {error:.6f} > {TOLERANCE:.6f}"
            )
            checked.append((sample["code"], minute["ts"]))

    assert {code for code, _ in checked} == EXPECTED_CODES
