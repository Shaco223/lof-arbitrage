from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FundType = Literal["index", "industry", "active", "qdii"]
SourceQuality = Literal["ok", "degraded", "stale"]


_TYPE_MAP = {
    "指数": "index",
    "指数型": "index",
    "index": "index",
    "行业": "industry",
    "行业型": "industry",
    "industry": "industry",
    "主动": "active",
    "主动型": "active",
    "active": "active",
    "QDII": "qdii",
    "qdii": "qdii",
}


@dataclass(frozen=True)
class CoverageInputs:
    fund_type: str
    top10_weight: float
    benchmark_assigned_weight: float
    cash_weight: float


@dataclass(frozen=True)
class CoverageBreakdown:
    top10_weight: float
    benchmark_assigned_weight: float
    cash_weight: float


@dataclass(frozen=True)
class CoverageResult:
    coverage: float
    breakdown: CoverageBreakdown
    formula: Literal["index", "active"]
    source_quality: SourceQuality


def normalize_fund_type(raw_type: str) -> FundType:
    normalized = _TYPE_MAP.get(str(raw_type).strip())
    if normalized is None:
        raise ValueError(f"unsupported fund type: {raw_type}")
    return normalized  # type: ignore[return-value]


def _clamp_weight(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return float(value)


def _round_ratio(value: float) -> float:
    return round(_clamp_weight(value), 6)


def calculate_coverage(inputs: CoverageInputs) -> CoverageResult:
    fund_type = normalize_fund_type(inputs.fund_type)
    top10_weight = _clamp_weight(inputs.top10_weight)
    benchmark_assigned_weight = _clamp_weight(inputs.benchmark_assigned_weight)
    cash_weight = _clamp_weight(inputs.cash_weight)
    benchmark_plus_cash = _clamp_weight(benchmark_assigned_weight + cash_weight)

    if fund_type in ("index", "qdii"):
        coverage = benchmark_plus_cash
        formula = "index"
    else:
        coverage = top10_weight + (1 - top10_weight) * benchmark_plus_cash
        formula = "active"

    coverage = _round_ratio(coverage)
    return CoverageResult(
        coverage=coverage,
        breakdown=CoverageBreakdown(
            top10_weight=_round_ratio(top10_weight),
            benchmark_assigned_weight=_round_ratio(benchmark_assigned_weight),
            cash_weight=_round_ratio(cash_weight),
        ),
        formula=formula,
        source_quality=quality_from_coverage(coverage),
    )


def quality_from_coverage(coverage: float) -> SourceQuality:
    if coverage >= 0.9:
        return "ok"
    if coverage >= 0.7:
        return "degraded"
    return "stale"
