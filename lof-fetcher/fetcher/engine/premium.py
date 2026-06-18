from __future__ import annotations


def calculate_premium(price: float, iopv: float) -> float:
    if iopv <= 0:
        raise ValueError("iopv must be greater than 0")
    return round((price - iopv) / iopv, 6)


def estimate_iopv(
    previous_nav: float,
    weighted_returns: list[float],
    uncovered_return: float = 0.0,
) -> float:
    if previous_nav <= 0:
        raise ValueError("previous_nav must be greater than 0")
    total_return = sum(weighted_returns) + uncovered_return
    return round(previous_nav * (1 + total_return), 6)
