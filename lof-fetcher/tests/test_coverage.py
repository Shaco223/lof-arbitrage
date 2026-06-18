from fetcher.engine.coverage import CoverageInputs, calculate_coverage, quality_from_coverage


def test_index_coverage_uses_benchmark_and_cash_only():
    inputs = CoverageInputs(
        fund_type="index",
        top10_weight=0.42,
        benchmark_assigned_weight=0.95,
        cash_weight=0.05,
    )

    result = calculate_coverage(inputs)

    assert result.coverage == 1.0
    assert result.breakdown.top10_weight == 0.42
    assert result.breakdown.benchmark_assigned_weight == 0.95
    assert result.breakdown.cash_weight == 0.05
    assert result.formula == "index"


def test_active_coverage_uses_top10_plus_benchmark_completion():
    inputs = CoverageInputs(
        fund_type="active",
        top10_weight=0.3,
        benchmark_assigned_weight=0.8,
        cash_weight=0.1,
    )

    result = calculate_coverage(inputs)

    assert result.coverage == 0.93
    assert result.formula == "active"


def test_coverage_is_capped_at_one():
    inputs = CoverageInputs(
        fund_type="industry",
        top10_weight=0.7,
        benchmark_assigned_weight=0.95,
        cash_weight=0.1,
    )

    result = calculate_coverage(inputs)

    assert result.coverage == 1.0


def test_quality_from_coverage_thresholds():
    assert quality_from_coverage(0.91) == "ok"
    assert quality_from_coverage(0.7) == "degraded"
    assert quality_from_coverage(0.69) == "stale"
