from __future__ import annotations

from fetcher.sources.qdii_estimate import (
    QDII_HIGH_CODES,
    QDII_OBSERVATION_CODES,
    QDII_REFERENCE_MAPPINGS,
    calculate_qdii_estimate,
    fetch_qdii_reference_payloads,
    parse_sina_fx_payload,
    parse_tencent_reference_index_payload,
    qdii_null_fields,
    qdii_observation_fields,
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


def test_qdii_high_scope_locked_to_prd_1_6_1_phase2():
    # PRD 1.6.1 扩至 12 只 (原 5 只 + 7 只新准入)
    assert QDII_HIGH_CODES == {
        "510900", "159920", "159941", "513500", "161125",
        "501225", "161126", "161127", "161128", "161130",
        "160125", "501312",
    }



def test_reference_index_and_fx_parsers_extract_change_pct():
    index_payload = 'v_hkHSCEI="100~????~HSCEI~7675.810~7558.300";v_usINX="200~??500~.INX~7483.23~7499.36";'
    fx_payload = 'var hq_str_fx_susdcny="09:50:01,6.7853,6.7863,6.7880,178,6.7938,6.7938,6.7760,6.7858,?????,-0.0324,-0.0022";'

    assert parse_tencent_reference_index_payload(index_payload) == {
        "hkHSCEI": 0.015547,
        "usINX": -0.002151,
    }
    assert parse_sina_fx_payload(fx_payload) == {"fx_susdcny": -0.000324}



def test_qdii_high_codes_are_present_in_default_watchlist():
    from fetcher.pipeline.real_watchlist import DEFAULT_WATCHLIST_PATH
    from fetcher.sources.csv_assets import load_watchlist

    metas = load_watchlist(DEFAULT_WATCHLIST_PATH)
    by_code = {meta.code: meta for meta in metas}

    assert QDII_HIGH_CODES <= set(by_code)
    assert {by_code[code].type for code in QDII_HIGH_CODES} == {"qdii"}



def test_qdii_high_names_are_not_mojibake_question_marks():
    from fetcher.pipeline.real_watchlist import DEFAULT_WATCHLIST_PATH
    from fetcher.sources.csv_assets import load_watchlist
    from fetcher.sources.qdii_estimate import QDII_REFERENCE_MAPPINGS

    metas = {meta.code: meta for meta in load_watchlist(DEFAULT_WATCHLIST_PATH)}
    for code in QDII_HIGH_CODES:
        assert code in metas
        assert "?" not in metas[code].name
        assert "?" not in metas[code].benchmark_raw
        assert "?" not in QDII_REFERENCE_MAPPINGS[code].reference_index_name



def test_qdii_observation_codes_scope_locked_to_prd_1_6_1():
    assert QDII_OBSERVATION_CODES == frozenset({
        "164824", "160140", "162415", "164906", "160644",
    })
    # 观察池代码 MUST NOT 出现在 high 名单
    assert QDII_HIGH_CODES.isdisjoint(QDII_OBSERVATION_CODES)


def test_qdii_observation_returns_not_supported_and_null_estimate():
    # 观察池标的即便传入完整 price / nav / index / fx, 也不做估算
    for code in ("164824", "160140", "162415", "164906", "160644"):
        result = calculate_qdii_estimate(
            code=code,
            price=1.2,
            nav_official=1.1,
            nav_official_date="2026-07-02",
            reference_index_change_pct=0.01,
            fx_change_pct=-0.001,
        )
        assert result["qdii_estimate_quality"] == "not_supported", code
        assert result["qdii_estimate_nav"] is None, code
        assert result["qdii_estimate_premium"] is None, code
        assert result["qdii_reference_index_code"] is None, code
        assert result["qdii_reference_index_change_pct"] is None, code
        assert result["qdii_fx_change_pct"] is None, code


def test_qdii_observation_fields_shape_matches_null_fields_keys():
    obs = qdii_observation_fields()
    nul = qdii_null_fields()
    assert set(obs) == set(nul)
    assert obs["qdii_estimate_quality"] == "not_supported"
    # null_fields 保持原 "unavailable" 语义 (无映射 / 缺参数)
    assert nul["qdii_estimate_quality"] == "unavailable"


def test_fetch_qdii_reference_payloads_skips_observation_codes(monkeypatch):
    called_with: list[list[str]] = []
    def stub(codes):
        called_with.append(codes)
        return {}
    # 不真的联网 — 通过替换 _fetch_reference_index_changes 拦截
    import fetcher.sources.qdii_estimate as mod
    def fake_indexes(client, codes):
        called_with.append(codes)
        return {}
    def fake_fx(client, codes):
        return {}
    monkeypatch.setattr(mod, "_fetch_reference_index_changes", fake_indexes)
    monkeypatch.setattr(mod, "_fetch_fx_changes", fake_fx)
    payloads = fetch_qdii_reference_payloads(
        ["501225", "164824", "160125", "164906", "163402"],
    )
    # 只保留 high 且非观察池, 观察池 (164824 / 164906) 和非 QDII (163402) 被剔除
    assert set(payloads) == {"501225", "160125"}
    assert called_with, "index fetch should still be invoked"
    assert set(called_with[0]) == {"501225", "160125"}


def test_qdii_1_6_1_new_high_names_present_in_watchlist():
    from fetcher.pipeline.real_watchlist import DEFAULT_WATCHLIST_PATH
    from fetcher.sources.csv_assets import load_watchlist
    metas = {meta.code: meta for meta in load_watchlist(DEFAULT_WATCHLIST_PATH)}
    new_codes = {"501225", "161126", "161127", "161128", "161130", "160125", "501312"}
    for code in new_codes:
        assert code in metas, f"missing {code} in watchlist"
        assert metas[code].type == "qdii", code
        assert "?" not in metas[code].name, code
        # 每只都能查到 QDII_REFERENCE_MAPPINGS
        assert code in QDII_REFERENCE_MAPPINGS


def test_qdii_1_6_1_observation_codes_present_in_watchlist_but_not_in_mappings():
    from fetcher.pipeline.real_watchlist import DEFAULT_WATCHLIST_PATH
    from fetcher.sources.csv_assets import load_watchlist
    metas = {meta.code: meta for meta in load_watchlist(DEFAULT_WATCHLIST_PATH)}
    for code in QDII_OBSERVATION_CODES:
        assert code in metas, f"observation {code} missing in watchlist"
        assert metas[code].type == "qdii", code
        assert code not in QDII_REFERENCE_MAPPINGS, code

