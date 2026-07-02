from __future__ import annotations

from fetcher.sources.qdii_estimate import (
    QDII_HIGH_CODES,
    calculate_qdii_estimate,
    parse_sina_fx_payload,
    parse_tencent_reference_index_payload,
    qdii_null_fields,
)


def test_qdii_estimate_formula_rounds_to_1e4_tolerance():
    result = calculate_qdii_estimate(
        code="510900",
        price=1.08,
        nav_official=1.0,
        nav_official_date="2026-07-01",
        reference_index_change_pct=0.02,
        fx_change_pct=0.01,
    )

    assert result["qdii_estimate_nav"] == 1.0302
    assert abs(result["qdii_estimate_premium"] - 0.04834) <= 1e-4
    assert result["qdii_reference_index_code"] == "hkHSCEI"
    assert result["qdii_estimate_quality"] == "high"


def test_qdii_estimate_null_for_non_high_code():
    result = calculate_qdii_estimate(
        code="162411",
        price=0.8,
        nav_official=0.82,
        nav_official_date="2026-07-01",
        reference_index_change_pct=-0.01,
        fx_change_pct=0.0,
    )

    assert result == qdii_null_fields()


def test_qdii_estimate_null_for_missing_nav_or_index_or_fx():
    base = dict(code="510900", price=1.0, nav_official=1.0, nav_official_date="2026-07-01")
    assert calculate_qdii_estimate(**base, reference_index_change_pct=None, fx_change_pct=0.0)["qdii_estimate_nav"] is None
    assert calculate_qdii_estimate(**{**base, "nav_official": None}, reference_index_change_pct=0.01, fx_change_pct=0.0)["qdii_estimate_nav"] is None
    assert calculate_qdii_estimate(**base, reference_index_change_pct=0.01, fx_change_pct=None)["qdii_estimate_nav"] is None


def test_qdii_high_scope_locked_to_prd_1_6_phase1():
    assert QDII_HIGH_CODES == {"510900", "159920", "159941", "513500", "161125"}



def test_reference_index_and_fx_parsers_extract_change_pct():
    index_payload = 'v_hkHSCEI="100~????~HSCEI~7675.810~7558.300";v_usINX="200~??500~.INX~7483.23~7499.36";'
    fx_payload = 'var hq_str_fx_susdcny="09:50:01,6.7853,6.7863,6.7880,178,6.7938,6.7938,6.7760,6.7858,?????,-0.0324,-0.0022";'

    assert parse_tencent_reference_index_payload(index_payload) == {
        "hkHSCEI": 0.015547,
        "usINX": -0.002151,
    }
    assert parse_sina_fx_payload(fx_payload) == {"fx_susdcny": -0.000324}
