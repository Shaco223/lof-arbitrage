import pytest

from fetcher.engine.premium import calculate_premium, estimate_iopv


def test_calculate_premium():
    assert calculate_premium(price=1.05, iopv=1.0) == 0.05
    assert calculate_premium(price=0.98, iopv=1.0) == -0.02


def test_calculate_premium_rejects_zero_iopv():
    with pytest.raises(ValueError):
        calculate_premium(price=1.0, iopv=0)


def test_estimate_iopv_applies_weighted_component_returns():
    assert estimate_iopv(
        previous_nav=1.0,
        weighted_returns=[0.03, -0.01],
        uncovered_return=0.0,
    ) == 1.02
