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
