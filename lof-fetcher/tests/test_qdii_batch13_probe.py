"""Offline unit tests for the QDII 13-batch reference-index probe.

Uses a stub fetcher (no real network) to verify:
  - Tencent index / Sina gb / Sina fx / fundgz parsers on canned payloads
  - build_item mixes jisilu-nav-first / fundgz-fallback correctly
  - classify_quality respects correlation + formula_type
  - run_probe with stub fetcher covers all 13 mappings deterministically
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

FETCHER_ROOT = Path(__file__).resolve().parents[1]
if str(FETCHER_ROOT) not in sys.path:
    sys.path.insert(0, str(FETCHER_ROOT))

# Load the probe module from scripts/ as a module for testing.
_SPEC = importlib.util.spec_from_file_location(
    "probe_qdii_batch13",
    FETCHER_ROOT / "scripts" / "probe_qdii_batch13.py",
)
_probe = importlib.util.module_from_spec(_SPEC)  # type: ignore[arg-type]
sys.modules["probe_qdii_batch13"] = _probe
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_probe)  # type: ignore[union-attr]


def test_parse_tencent_index_payload_reads_change_pct():
    payload = (
        'v_usINX="200~S&P500~.INX~7500.00~7400.00~7495.14~3414~0~0~7425.05~0~0~0~0~0~0~0'
        '~0~0~7511.57~0~0~0~0~0~0~0~0~0~~2026-07-02 16:42:15~0.01~0.00~7540.75~7427.55~USD";'
    )
    parsed = _probe.parse_tencent_index_payload(payload)
    assert "usINX" in parsed
    assert parsed["usINX"]["price"] == 7500.0
    assert parsed["usINX"]["previous_close"] == 7400.0
    assert parsed["usINX"]["change_pct"] == round(7500.0 / 7400.0 - 1, 6)


def test_parse_sina_gb_payload_uses_percent_field():
    payload = (
        'var hq_str_gb_ndx="Nasdaq100,29329.2129,-1.61,2026-07-03 05:30:00,-479.9,'
        '29778.6951,30044.4987,29087.3267,30762.19,22587.47";'
    )
    parsed = _probe.parse_sina_gb_payload(payload)
    assert parsed["gb_ndx"]["price"] == 29329.2129
    assert parsed["gb_ndx"]["change_pct"] == round(-1.61 / 100, 6)


def test_parse_sina_fx_payload_reads_pct():
    payload = (
        'var hq_str_fx_susdcny="15:04:31,6.7797,6.7807,6.7909,245,6.7881,6.7914,'
        '6.7669,6.7802,USDCNY,-0.1576,-0.0107,0.0245,note,0,0,,2026-07-03";'
    )
    parsed = _probe.parse_sina_fx_payload(payload)
    assert parsed["fx_susdcny"]["rate"] == 6.7797
    assert parsed["fx_susdcny"]["change_pct"] == round(-0.1576 / 100, 6)


def test_parse_fundgz_empty_body():
    assert _probe.parse_fundgz_payload("jsonpgz();") == {"ok": False, "reason": "empty_jsonpgz"}
    assert _probe.parse_fundgz_payload("jsonpgz();\n")["ok"] is False


def test_parse_fundgz_reads_dwjz_and_jzrq():
    text = 'jsonpgz({"fundcode":"161125","name":"n","jzrq":"2026-07-01","dwjz":"3.0893","gsz":"3.11"});'
    parsed = _probe.parse_fundgz_payload(text)
    assert parsed["ok"] is True
    assert parsed["fund_nav_t1"] == 3.0893
    assert parsed["nav_dt"] == "2026-07-01"


def test_calculate_estimate_and_rejects_missing():
    result = _probe.calculate_estimate(price=3.126, fund_nav_t1=3.0768, index_change_pct=0.0079, fx_change_pct=0.000972)
    assert result["estimate_nav"] == round(3.0768 * 1.0079 * 1.000972, 6)
    assert result["estimate_premium"] == round(3.126 / result["estimate_nav"] - 1, 6)
    missing = _probe.calculate_estimate(price=1.0, fund_nav_t1=None, index_change_pct=0.01, fx_change_pct=0.0)
    assert missing["estimate_nav"] is None and missing["estimate_premium"] is None


def test_classify_quality_matrix():
    q = _probe.classify_quality
    assert q(nav_ok=True, primary_index_ok=True, fx_ok=True, correlation="strong", formula_type="index") == "high"
    assert q(nav_ok=True, primary_index_ok=True, fx_ok=False, correlation="strong", formula_type="index") == "medium"
    assert q(nav_ok=True, primary_index_ok=True, fx_ok=True, correlation="medium", formula_type="index") == "medium"
    assert q(nav_ok=True, primary_index_ok=True, fx_ok=True, correlation="weak", formula_type="mixed") == "low"
    assert q(nav_ok=False, primary_index_ok=True, fx_ok=True, correlation="strong", formula_type="index") == "unavailable"
    assert q(nav_ok=True, primary_index_ok=False, fx_ok=True, correlation="strong", formula_type="index") == "unavailable"


class _StubFetcher:
    """In-memory fetcher matching _Fetcher's public methods."""

    def __init__(self, *, price_map, fundgz_map, jisilu_map, tencent_index_map, sina_gb_map, fx_map):
        self._price_map = price_map
        self._fundgz_map = fundgz_map
        self._jisilu_map = jisilu_map
        self._tencent_index_map = tencent_index_map
        self._sina_gb_map = sina_gb_map
        self._fx_map = fx_map

    def close(self):
        pass

    def fetch_market_price(self, code):
        return self._price_map.get(code, {"ok": False, "price": None})

    def fetch_tencent_indexes(self, symbols):
        return {s: self._tencent_index_map[s] for s in symbols if s in self._tencent_index_map}

    def fetch_sina_gb(self, symbols):
        return {s: self._sina_gb_map[s] for s in symbols if s in self._sina_gb_map}

    def fetch_sina_fx(self, symbols):
        return {s: self._fx_map[s] for s in symbols if s in self._fx_map}

    def fetch_fundgz(self, code):
        return self._fundgz_map.get(code, {"ok": False, "reason": "empty_jsonpgz"})

    def fetch_jisilu_qdii(self, cookie):
        return self._jisilu_map


def _stub_for_run():
    price = {m.code: {"ok": True, "price": 1.0 + i * 0.01, "change_pct": 0.001, "amount": 1000.0}
             for i, m in enumerate(_probe.BATCH13_MAPPINGS)}
    fundgz = {m.code: {"ok": True, "fund_nav_t1": 2.0, "nav_dt": "2026-07-01", "name": m.name}
              for m in _probe.BATCH13_MAPPINGS}
    jisilu = {m.code: {"fund_nav": 2.5, "nav_dt": "2026-07-02", "name": m.name,
                       "index_id": "IDX", "index_nm": "IDX_NM"}
              for m in _probe.BATCH13_MAPPINGS}
    tencent_index = {}
    sina_gb = {}
    for m in _probe.BATCH13_MAPPINGS:
        for c in m.candidates:
            if c.source == "tencent":
                tencent_index[c.symbol] = {"price": 100.0, "previous_close": 99.0, "change_pct": 0.010101,
                                           "name": c.display_name, "quote_time": ""}
            elif c.source == "sina_gb":
                sina_gb[c.symbol] = {"price": 100.0, "change_pct": 0.005, "name": c.display_name, "quote_time": ""}
    fx = {"fx_susdcny": {"rate": 6.78, "change_pct": 0.001, "quote_time": ""},
          "fx_shkdcny": {"rate": 0.865, "change_pct": -0.002, "quote_time": ""}}
    return _StubFetcher(price_map=price, fundgz_map=fundgz, jisilu_map=jisilu,
                        tencent_index_map=tencent_index, sina_gb_map=sina_gb, fx_map=fx)


def test_run_probe_covers_all_13_and_uses_jisilu_nav_when_present(monkeypatch):
    monkeypatch.delenv("JISILU_COOKIE", raising=False)
    report = _probe.run_probe(fetcher=_stub_for_run())
    assert report["sample_count"] == 13
    codes = [it["code"] for it in report["items"]]
    assert set(codes) == {m.code for m in _probe.BATCH13_MAPPINGS}
    # All items get jisilu nav in stub -> nav_source == 'jisilu_qdii'
    assert all(it["nav_source"] == "jisilu_qdii" for it in report["items"])
    # 161125 (strong, index) -> high; 164906 / 160644 (weak/mixed/hybrid) -> low
    quality_by_code = {it["code"]: it["estimate_quality"] for it in report["items"]}
    assert quality_by_code["161125"] == "high"
    assert quality_by_code["164906"] == "low"
    assert quality_by_code["160644"] == "low"
    # 164824 (regional/medium) -> medium
    assert quality_by_code["164824"] == "medium"
    # 160140 (index/medium) -> medium
    assert quality_by_code["160140"] == "medium"


def test_build_item_falls_back_to_fundgz_when_no_jisilu_row():
    mapping = next(m for m in _probe.BATCH13_MAPPINGS if m.code == "161125")
    price = {"ok": True, "price": 3.126, "change_pct": 0.0032, "amount": 10090000.0}
    fundgz = {"ok": True, "fund_nav_t1": 3.0768, "nav_dt": "2026-07-01", "name": "n"}
    tencent_map = {"usINX": {"price": 7500.0, "previous_close": 7400.0, "change_pct": 0.013514, "name": "sp500", "quote_time": ""}}
    fx = {"fx_susdcny": {"rate": 6.78, "change_pct": 0.001, "quote_time": ""}}
    item = _probe.build_item(mapping, price_info=price, fundgz_info=fundgz, jisilu_row=None,
                              tencent_index_map=tencent_map, sina_gb_map={}, fx_map=fx, cookie_present=False)
    assert item["nav_source"] == "fundgz"
    assert item["fund_nav_t1"] == 3.0768
    assert item["reference_index_symbol"] == "usINX"
    assert item["estimate_nav"] == round(3.0768 * (1 + 0.013514) * (1 + 0.001), 6)
    assert item["estimate_premium"] == round(3.126 / item["estimate_nav"] - 1, 6)
    assert item["estimate_quality"] == "high"


def test_build_item_returns_unavailable_when_nav_missing():
    mapping = next(m for m in _probe.BATCH13_MAPPINGS if m.code == "501225")
    price = {"ok": True, "price": 1.5, "change_pct": 0.0}
    fundgz = {"ok": False, "reason": "empty_jsonpgz"}
    tencent_map = {"usSOXX": {"price": 566.0, "previous_close": 599.0, "change_pct": -0.055, "name": "SOXX", "quote_time": ""}}
    fx = {"fx_susdcny": {"rate": 6.78, "change_pct": 0.001, "quote_time": ""}}
    item = _probe.build_item(mapping, price_info=price, fundgz_info=fundgz, jisilu_row=None,
                              tencent_index_map=tencent_map, sina_gb_map={}, fx_map=fx, cookie_present=False)
    assert item["nav_source"] is None
    assert item["fund_nav_t1"] is None
    assert item["estimate_nav"] is None
    assert item["estimate_quality"] == "unavailable"
    assert "missing_nav_no_cookie_jisilu_truncated" in item["reasons"] or "fundgz_empty_jsonpgz" in item["reasons"]


def test_reports_scope_and_ccr_are_readonly():
    stub = _stub_for_run()
    report = _probe.run_probe(fetcher=stub)
    assert report["ccr"].startswith("not_triggered")
    assert "read" in report["scope"].lower() or "只读" in report["scope"]
    assert report["disclaimer"] == "参考指数估算, 非交易所 IOPV"


def test_render_markdown_contains_all_codes():
    stub = _stub_for_run()
    report = _probe.run_probe(fetcher=stub)
    md = _probe.render_markdown(report)
    for m in _probe.BATCH13_MAPPINGS:
        assert m.code in md
    assert "非交易所 IOPV" in md
    assert "推荐 high 准入清单" in md

# ---------------------------------------------------------------------------
# v2: 混合口径复合指数拟合 + E 类补测 + hists 抽取 单测
# ---------------------------------------------------------------------------


def test_fit_two_factor_ols_recovers_known_weights():
    # y = 0.7 * a + 0.3 * b, 无噪
    a = [0.01, -0.02, 0.03, -0.01, 0.02, 0.005, -0.015]
    b = [-0.01, 0.01, 0.02, 0.0, -0.02, 0.008, 0.003]
    y = [0.7 * a[i] + 0.3 * b[i] for i in range(len(a))]
    r = _probe.fit_two_factor_ols(y, a, b)
    assert r is not None
    assert abs(r["w_a"] - 0.7) < 1e-9
    assert abs(r["w_b"] - 0.3) < 1e-9
    assert r["rmse"] < 1e-9
    assert r["n"] == len(y)


def test_fit_two_factor_ols_returns_none_on_length_mismatch():
    assert _probe.fit_two_factor_ols([0.01], [], []) is None
    assert _probe.fit_two_factor_ols([0.01, 0.02], [0.01], [0.01, 0.02]) is None


def test_grid_search_two_factor_bounds_and_sum_to_one():
    a = [0.01, -0.02, 0.03]
    b = [-0.01, 0.01, 0.02]
    y = [0.5 * a[i] + 0.5 * b[i] for i in range(len(a))]
    g = _probe.grid_search_two_factor(y, a, b, w_a_lo=0.3, w_a_hi=0.7, step=0.05, sum_to_one=True)
    assert g["best"]["w_a"] == 0.5
    assert g["best"]["w_b"] == 0.5
    # 全部 trial 均 sum_to_one
    for t in g["trials"]:
        assert abs(t["w_a"] + t["w_b"] - 1.0) < 1e-6
        assert 0.3 - 1e-6 <= t["w_a"] <= 0.7 + 1e-6
    # 网格步长与端点
    assert len(g["trials"]) == 9  # 0.30 ... 0.70 step 0.05


def test_classify_composite_quality_thresholds():
    assert _probe.classify_composite_quality(0.001) == "medium"
    assert _probe.classify_composite_quality(0.004) == "medium"
    assert _probe.classify_composite_quality(0.009) == "medium"
    assert _probe.classify_composite_quality(0.010) == "low"
    assert _probe.classify_composite_quality(0.05) == "low"


def test_extract_daily_fund_and_ref_from_hists():
    # 三天净值 -> 两天日收益; ref_increase_rt 百分比自动换算
    hists = [
        {"net_value": "1.000", "net_value_dt": "2026-06-30", "ref_increase_rt": "0.5"},
        {"net_value": "1.010", "net_value_dt": "2026-07-01", "ref_increase_rt": "1.0"},
        {"net_value": "1.020", "net_value_dt": "2026-07-02", "ref_increase_rt": "-0.5"},
    ]
    daily = _probe._extract_daily_fund_and_ref(hists)
    assert len(daily) == 2
    assert daily[0][0] == "2026-07-01"
    assert abs(daily[0][1] - (1.010 / 1.000 - 1)) < 1e-9
    assert abs(daily[0][2] - 0.010) < 1e-9  # 1.0% -> 0.01
    assert daily[1][0] == "2026-07-02"
    assert abs(daily[1][2] - (-0.005)) < 1e-9


def test_extract_daily_fund_and_ref_skips_missing_fields():
    hists = [
        {"net_value": None, "net_value_dt": "2026-06-30", "ref_increase_rt": "0.5"},
        {"net_value": "1.010", "net_value_dt": None, "ref_increase_rt": "1.0"},
        {"net_value": "1.020", "net_value_dt": "2026-07-02", "ref_increase_rt": None},
    ]
    assert _probe._extract_daily_fund_and_ref(hists) == []


class _StubV2Fetcher(_StubFetcher):
    """StubFetcher 扩展: 提供 fetch_detail_hists / fetch_tencent_hk_daily。"""

    def __init__(self, *, hists_by_code, hk_daily, **kw):
        super().__init__(**kw)
        self._hists = hists_by_code
        self._hk_daily = hk_daily

    def fetch_detail_hists(self, code, cookie, rp=60):
        return self._hists.get(code, [])

    def fetch_tencent_hk_daily(self, symbol, limit=60):
        return self._hk_daily if symbol == "hkHSTECH" else {}


def _stub_v2():
    price = {m.code: {"ok": True, "price": 1.0, "change_pct": 0.001, "amount": 1000.0}
             for m in _probe.BATCH13_MAPPINGS}
    fundgz = {m.code: {"ok": True, "fund_nav_t1": 2.0, "nav_dt": "2026-07-01", "name": m.name}
              for m in _probe.BATCH13_MAPPINGS}
    jisilu = {m.code: {"fund_nav": 2.5, "nav_dt": "2026-07-02", "name": m.name,
                       "index_id": "IDX", "index_nm": "IDX_NM"}
              for m in _probe.BATCH13_MAPPINGS}
    tencent_index = {}
    for m in _probe.BATCH13_MAPPINGS:
        for c in m.candidates:
            if c.source == "tencent":
                tencent_index[c.symbol] = {"price": 100.0, "previous_close": 99.0,
                                           "change_pct": 0.010101, "name": c.display_name, "quote_time": ""}
    fx = {"fx_susdcny": {"rate": 6.78, "change_pct": 0.001, "quote_time": ""},
          "fx_shkdcny": {"rate": 0.865, "change_pct": -0.002, "quote_time": ""}}
    # 构造 hists: 5 天净值序列 (含两个 code)
    def _hists(code):
        # 生成 y = 0.6 * ref + 0.4 * hs 的净值序列
        rets_ref = [0.005, -0.003, 0.006, -0.002, 0.004]
        rets_hs = [-0.002, 0.004, -0.001, 0.003, -0.002]
        dates = ["2026-06-26", "2026-06-27", "2026-06-28", "2026-06-29", "2026-06-30"]
        nv = 1.0
        rows = [{"net_value": "1.000", "net_value_dt": "2026-06-25", "ref_increase_rt": "0.0"}]
        for i, d in enumerate(dates):
            y = 0.6 * rets_ref[i] + 0.4 * rets_hs[i]
            nv *= (1 + y)
            rows.append({
                "net_value": f"{nv:.6f}",
                "net_value_dt": d,
                "ref_increase_rt": f"{rets_ref[i] * 100:.6f}",
            })
        return rows
    hists_by_code = {"164906": _hists("164906"), "160644": _hists("160644")}
    hk_daily = {
        "2026-06-26": -0.002, "2026-06-27": 0.004, "2026-06-28": -0.001,
        "2026-06-29": 0.003, "2026-06-30": -0.002,
    }
    return _StubV2Fetcher(
        price_map=price, fundgz_map=fundgz, jisilu_map=jisilu,
        tencent_index_map=tencent_index, sina_gb_map={}, fx_map=fx,
        hists_by_code=hists_by_code, hk_daily=hk_daily,
    )


def test_run_composite_fitting_returns_two_codes_and_low_rmse():
    stub = _stub_v2()
    results = _probe.run_composite_fitting(stub, cookie=None)
    assert [r["code"] for r in results] == ["164906", "160644"]
    for r in results:
        assert r["aligned_sample_size"] == 5
        # 构造的 y = 0.6 * ref + 0.4 * hs, OLS 应该恢复精确权重
        ols = r["ols"]
        assert ols is not None
        assert abs(ols["w_ref"] - 0.6) < 1e-3
        assert abs(ols["w_hs"] - 0.4) < 1e-3
        assert r["rmse_ref_only"] is not None
        # 网格最优 w_ref=0.6 命中
        assert r["grid"]["best"]["w_ref"] == 0.6
        assert r["composite_quality"] == "medium"


def test_build_report_v2_marks_e_class_upgrade_and_ccr():
    stub = _stub_v2()
    base = _probe.run_probe(fetcher=stub)
    composite = _probe.run_composite_fitting(stub, cookie=None)
    report = _probe.build_report_v2(base, composite)
    assert report["version"] == "v2"
    assert "E 类" in report["scope"] or "E-category" in report["scope"] or "category=E" in report["e_class_probe"]["note"]
    # stub 给每只都填 jisilu.fund_nav, 所以 501225 / 164824 都会被判定为非 unavailable
    recovered = report["e_class_probe"]["recovered_codes"]
    assert "501225" in recovered
    assert "164824" in recovered
    # 质量矩阵包含全部 13 只
    codes_in_matrix = {row["code"] for row in report["quality_matrix_v1_vs_v2"]}
    assert codes_in_matrix == {m.code for m in _probe.BATCH13_MAPPINGS}
    # 结构性建议 CCR 标记
    assert report["structural_recommendation"]["ccr_required"] is True
    assert "1.6.2" in report["structural_recommendation"]["ccr_target"]
    assert report["ccr"].startswith("not_triggered")


def test_render_markdown_v2_contains_key_sections():
    stub = _stub_v2()
    base = _probe.run_probe(fetcher=stub)
    composite = _probe.run_composite_fitting(stub, cookie=None)
    report = _probe.build_report_v2(base, composite)
    md = _probe.render_markdown_v2(report)
    assert "QDII 13" in md and "v2" in md
    assert "E 类接口补测" in md
    assert "混合口径复合指数拟合" in md
    assert "质量矩阵 v1 vs v2" in md
    assert "结构性建议" in md
    assert "非交易所 IOPV" in md


def test_fetch_jisilu_qdii_iterates_categories_and_prefers_nav():
    calls: list[str] = []

    class _CatClient:
        def get(self, url, params=None, headers=None):
            calls.append(url)
            if url.endswith("/qdii_list/"):
                rows = [
                    {"cell": {"fund_id": "161125", "fund_nav": "3.0768", "nav_dt": "2026-07-01", "fund_nm": "标普500"}},
                    {"cell": {"fund_id": "501225", "fund_nav": None, "nav_dt": "", "fund_nm": "全球芯片"}},
                ]
            elif url.endswith("/qdii_list/E"):
                assert params and params.get("only_lof") == "y"
                rows = [
                    {"cell": {"fund_id": "501225", "fund_nav": "3.5887", "nav_dt": "2026-07-01", "fund_nm": "全球芯片LOF"}},
                    {"cell": {"fund_id": "164824", "fund_nav": "1.3111", "nav_dt": "2026-07-01", "fund_nm": "印度基金"}},
                ]
            else:
                rows = []
            return _Resp({"rows": rows})

    class _Resp:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    fetcher = _probe._Fetcher(client=_CatClient())
    merged = fetcher.fetch_jisilu_qdii(cookie=None)
    fetcher.close()
    # 默认 + E 两轮
    assert any(u.endswith("/qdii_list/") for u in calls)
    assert any(u.endswith("/qdii_list/E") for u in calls)
    # 501225 应取 E 类的 fund_nav 而非默认的 None
    assert merged["501225"]["fund_nav"] == 3.5887
    assert merged["501225"]["category_source"] == "E"
    # 161125 保留默认类目
    assert merged["161125"]["fund_nav"] == 3.0768
    assert merged["161125"]["category_source"] == "default"
    assert merged["164824"]["fund_nav"] == 1.3111