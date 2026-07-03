"""QDII 13-only reference-index free-source batch probe (POC, read-only).

Scope (PM task 2026-07-03):
  Probe 13 QDII / cross-border LOF codes for whether a stable *free* real-time
  reference index (plus T-1 official NAV + FX change) allows us to compute
  qdii_estimate_nav = fund_nav_t1 * (1 + index_pct) * (1 + fx_pct).

  Read-only, does NOT touch:
    - real_watchlist main chain
    - QDII_REFERENCE_MAPPINGS (frozen by PRD 1.6 phase-1)
    - lof-watchlist-v2.csv
    - PRD section 6 fields

Cookie policy:
  JISILU_COOKIE is read ONLY from os.environ. Never logged / written to
  files / reports / test snapshots. Anonymous jisilu access returns the
  guest-truncated first 20 rows only; that is captured as a data-source
  limitation, not a bug.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import httpx

FETCHER_ROOT = Path(__file__).resolve().parents[1]
if str(FETCHER_ROOT) not in sys.path:
    sys.path.insert(0, str(FETCHER_ROOT))

UA = {"User-Agent": "Mozilla/5.0"}
SINA_HEADERS = {**UA, "Referer": "https://finance.sina.com.cn/"}
JISILU_QDII_LIST_URL = "https://www.jisilu.cn/data/qdii/qdii_list/"
JISILU_QDII_LIST_CATEGORIES: tuple[str, ...] = ("", "E")
JISILU_QDII_DETAIL_HISTS_URL = "https://www.jisilu.cn/data/qdii/detail_hists/{code}"
TENCENT_HK_KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get"
JISILU_QDII_REFERER = "https://www.jisilu.cn/data/qdii/"
FUNDGZ_URL = "https://fundgz.1234567.com.cn/js/{code}.js"
TENCENT_QUOTE_URL = "https://qt.gtimg.cn/q={symbols}"
SINA_LIST_URL = "https://hq.sinajs.cn/list={symbols}"


@dataclass(frozen=True)
class IndexCandidate:
    """One free-source reference-index candidate for a fund."""
    symbol: str
    display_name: str
    source: str
    cookie_required: bool = False
    correlation_note: str = ""


@dataclass(frozen=True)
class Batch13Mapping:
    code: str
    name: str
    asset_region: str
    currency: str
    fx_pair: str | None
    formula_type: str
    single_index_correlation: str
    candidates: tuple[IndexCandidate, ...]
    note: str = ""


BATCH13_MAPPINGS: tuple[Batch13Mapping, ...] = (
    Batch13Mapping(
        code="501225",
        name="全球芯片LOF",
        asset_region="us",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="index",
        single_index_correlation="strong",
        candidates=(
            IndexCandidate("usSOXX", "iShares 费城半导体 ETF (SOXX)", "tencent",
                           correlation_note="半导体宽基代理指数"),
            IndexCandidate("gb_soxx", "费城半导体 ETF (新浪 gb_soxx)", "sina_gb"),
            IndexCandidate("usSMH", "VanEck 半导体 ETF (SMH)", "tencent",
                           correlation_note="备用半导体宽基代理"),
        ),
    ),
    Batch13Mapping(
        code="161127",
        name="标普生物科技LOF",
        asset_region="us",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="index",
        single_index_correlation="strong",
        candidates=(
            IndexCandidate("usXBI", "SPDR 标普生物科技 ETF (XBI)", "tencent",
                           correlation_note="跟踪 SPSIBI 的宽基 ETF 代理"),
            IndexCandidate("gb_xbi", "SPDR 标普生物科技 ETF (新浪 gb_xbi)", "sina_gb"),
            IndexCandidate("usIBB", "iShares 生物技术 ETF (IBB)", "tencent",
                           correlation_note="纳斯达克生物技术备用代理"),
        ),
    ),
    Batch13Mapping(
        code="161126",
        name="标普医疗保健LOF",
        asset_region="us",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="index",
        single_index_correlation="strong",
        candidates=(
            IndexCandidate("usXLV", "SPDR 医疗保健精选 ETF (XLV)", "tencent",
                           correlation_note="标普医疗保健行业代理指数"),
            IndexCandidate("gb_xlv", "SPDR 医疗保健精选 ETF (新浪 gb_xlv)", "sina_gb"),
        ),
    ),
    Batch13Mapping(
        code="161130",
        name="纳指100LOF",
        asset_region="us",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="index",
        single_index_correlation="strong",
        candidates=(
            IndexCandidate("usNDX", "纳斯达克100 (NDX)", "tencent",
                           correlation_note="直接跟踪指数"),
            IndexCandidate("gb_ndx", "纳斯达克100 (新浪 gb_ndx)", "sina_gb"),
        ),
    ),
    Batch13Mapping(
        code="161125",
        name="标普500LOF",
        asset_region="us",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="index",
        single_index_correlation="strong",
        candidates=(
            IndexCandidate("usINX", "标普500 (INX)", "tencent",
                           correlation_note="直接跟踪指数; 回归对照"),
            IndexCandidate("gb_inx", "标普500 (新浪 gb_inx)", "sina_gb"),
        ),
        note="回归对照: 现有 QDII_REFERENCE_MAPPINGS high 标的",
    ),
    Batch13Mapping(
        code="164906",
        name="中概互联网LOF",
        asset_region="us_hk_mixed",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="mixed",
        single_index_correlation="weak",
        candidates=(
            IndexCandidate("usKWEB", "KraneShares 中概互联网 ETF (KWEB)", "tencent",
                           correlation_note="单一美股中概 ETF 代理; 港股中概敞口未覆盖"),
            IndexCandidate("gb_kweb", "KraneShares KWEB (新浪 gb_kweb)", "sina_gb"),
        ),
        note="混合口径: 美股中概 + 港股中概; 单一 KWEB 拟合误差偏大",
    ),
    Batch13Mapping(
        code="161128",
        name="标普信息科技LOF",
        asset_region="us",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="index",
        single_index_correlation="strong",
        candidates=(
            IndexCandidate("usXLK", "SPDR 科技精选 ETF (XLK)", "tencent",
                           correlation_note="标普信息科技行业代理"),
            IndexCandidate("gb_xlk", "SPDR 科技精选 ETF (新浪 gb_xlk)", "sina_gb"),
            IndexCandidate("usIYW", "iShares 美国科技 ETF (IYW)", "tencent",
                           correlation_note="备用美国科技代理"),
        ),
    ),
    Batch13Mapping(
        code="160140",
        name="美国REIT精选LOF",
        asset_region="us",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="index",
        single_index_correlation="medium",
        candidates=(
            IndexCandidate("usVNQ", "Vanguard 美国地产 ETF (VNQ)", "tencent",
                           correlation_note="美国 REIT 宽基代理; 与精选子集有跟踪误差"),
            IndexCandidate("gb_vnq", "VNQ (新浪 gb_vnq)", "sina_gb"),
        ),
    ),
    Batch13Mapping(
        code="164824",
        name="印度基金LOF",
        asset_region="india",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="regional",
        single_index_correlation="medium",
        candidates=(
            IndexCandidate("usINDA", "iShares MSCI 印度 ETF (INDA)", "tencent",
                           correlation_note="MSCI 印度宽基 ETF 代理; 与 SENSEX/NIFTY 高度相关"),
            IndexCandidate("gb_inda", "iShares MSCI 印度 ETF (新浪 gb_inda)", "sina_gb"),
        ),
        note="POC v1 曾标 unavailable; 本次复测尝试 usINDA / gb_inda 代理",
    ),
    Batch13Mapping(
        code="162415",
        name="美国消费LOF",
        asset_region="us",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="index",
        single_index_correlation="medium",
        candidates=(
            IndexCandidate("usXLY", "SPDR 可选消费精选 ETF (XLY)", "tencent",
                           correlation_note="消费行业宽基代理; 标普美国消费口径可能包含必需消费"),
            IndexCandidate("gb_xly", "SPDR 可选消费精选 ETF (新浪 gb_xly)", "sina_gb"),
        ),
    ),
    Batch13Mapping(
        code="160125",
        name="南方香港LOF",
        asset_region="hong_kong",
        currency="HKD",
        fx_pair="HKD/CNY",
        formula_type="index",
        single_index_correlation="strong",
        candidates=(
            IndexCandidate("hkHSI", "恒生指数 (HSI)", "tencent",
                           correlation_note="恒生宽基指数"),
            IndexCandidate("hkHSCEI", "恒生中国企业指数 (HSCEI)", "tencent",
                           correlation_note="国企指数备用"),
        ),
    ),
    Batch13Mapping(
        code="501312",
        name="海外科技LOF",
        asset_region="us",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="index",
        single_index_correlation="strong",
        candidates=(
            IndexCandidate("usXLK", "SPDR 科技精选 ETF (XLK)", "tencent",
                           correlation_note="美国科技行业代理"),
            IndexCandidate("gb_xlk", "SPDR 科技精选 ETF (新浪 gb_xlk)", "sina_gb"),
            IndexCandidate("usIYW", "iShares 美国科技 ETF (IYW)", "tencent",
                           correlation_note="备用美国科技代理"),
        ),
    ),
    Batch13Mapping(
        code="160644",
        name="港美互联网LOF",
        asset_region="us_hk_mixed",
        currency="USD",
        fx_pair="USD/CNY",
        formula_type="hybrid",
        single_index_correlation="weak",
        candidates=(
            IndexCandidate("usKWEB", "KraneShares 中概互联网 ETF (KWEB)", "tencent",
                           correlation_note="美股中概代理"),
            IndexCandidate("hkHSTECH", "恒生科技指数 (HSTECH)", "tencent",
                           correlation_note="港股互联网科技代理"),
        ),
        note="混合口径: 港股互联网 + 美股中概; 单一指数拟合误差大",
    ),
)


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "--", " "):
            return None
        text = str(value).strip().replace(",", "")
        if text.endswith("%"):
            text = text[:-1]
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_tencent_index_payload(text: str) -> dict[str, dict[str, Any]]:
    """Parse `v_<symbol>="a~b~..."` lines from qt.gtimg.cn.

    Returns a mapping symbol -> {price, previous_close, change_pct, name, quote_time}
    with change_pct rounded to 6 decimals when both price and previous_close exist.
    """
    result: dict[str, dict[str, Any]] = {}
    for symbol, payload in re.findall(r'v_([A-Za-z0-9_.^]+)="([^"]*)";?', text):
        fields = payload.split("~")
        if len(fields) < 6:
            continue
        price = to_float(fields[3])
        previous_close = to_float(fields[4])
        name = fields[1] if len(fields) > 1 else ""
        change_pct = None
        if price is not None and previous_close and previous_close > 0:
            change_pct = round(price / previous_close - 1, 6)
        quote_time = fields[30] if len(fields) > 30 else ""
        result[symbol] = {
            "price": price,
            "previous_close": previous_close,
            "change_pct": change_pct,
            "name": name,
            "quote_time": quote_time,
        }
    return result


def parse_sina_gb_payload(text: str) -> dict[str, dict[str, Any]]:
    """Parse `var hq_str_gb_xxx="name,price,pct_str,ts,delta,...,prev_close"` lines."""
    result: dict[str, dict[str, Any]] = {}
    for symbol, payload in re.findall(r'hq_str_(gb_[a-z0-9_]+)="([^"]*)";?', text):
        fields = payload.split(",")
        if len(fields) < 8:
            result[symbol] = {"price": None, "change_pct": None, "name": "", "quote_time": ""}
            continue
        name = fields[0]
        price = to_float(fields[1])
        pct_display = to_float(fields[2])
        change_pct = round(pct_display / 100, 6) if pct_display is not None else None
        result[symbol] = {
            "price": price,
            "change_pct": change_pct,
            "name": name,
            "quote_time": fields[3] if len(fields) > 3 else "",
        }
    return result


def parse_sina_fx_payload(text: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for symbol, payload in re.findall(r'hq_str_(fx_s[a-z0-9]+cny)="([^"]*)";?', text):
        fields = payload.split(",")
        if len(fields) < 12:
            continue
        rate = to_float(fields[1])
        pct_display = to_float(fields[10])
        change_pct = round(pct_display / 100, 6) if pct_display is not None else None
        result[symbol] = {
            "rate": rate,
            "change_pct": change_pct,
            "quote_time": fields[0] if fields else "",
        }
    return result


def parse_fundgz_payload(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.replace("\n", "") in ("jsonpgz();",):
        return {"ok": False, "reason": "empty_jsonpgz"}
    match = re.search(r"jsonpgz\((.*)\);?", stripped)
    if not match:
        return {"ok": False, "reason": "no_match"}
    body = match.group(1).strip()
    if not body:
        return {"ok": False, "reason": "empty_jsonpgz"}
    try:
        raw = json.loads(body)
    except (ValueError, TypeError):
        return {"ok": False, "reason": "parse_error"}
    return {
        "ok": to_float(raw.get("dwjz")) is not None,
        "fund_nav_t1": to_float(raw.get("dwjz")),
        "nav_dt": raw.get("jzrq") or "",
        "name": raw.get("name") or "",
    }


def market_symbol(code: str) -> str:
    return f"sh{code}" if code.startswith(("50", "51", "52")) else f"sz{code}"


def parse_tencent_quote_payload(text: str) -> dict[str, dict[str, Any]]:
    """Reused shape from qdii_reference_estimate probe (price, prev_close, amount)."""
    result: dict[str, dict[str, Any]] = {}
    for symbol, payload in re.findall(r'v_([A-Za-z0-9_.^]+)="([^"]*)";?', text):
        fields = payload.split("~")
        if len(fields) < 6:
            continue
        price = to_float(fields[3])
        previous_close = to_float(fields[4])
        pct = None
        if price is not None and previous_close and previous_close > 0:
            pct = round(price / previous_close - 1, 6)
        amount = None
        if len(fields) > 37:
            amount_wan = to_float(fields[37])
            amount = round(amount_wan * 10000, 2) if amount_wan is not None else None
        result[symbol] = {
            "price": price,
            "previous_close": previous_close,
            "change_pct": pct,
            "amount": amount,
            "name": fields[1] if len(fields) > 1 else "",
            "quote_time": fields[30] if len(fields) > 30 else "",
        }
    return result


def calculate_estimate(
    price: float | None,
    fund_nav_t1: float | None,
    index_change_pct: float | None,
    fx_change_pct: float | None,
) -> dict[str, float | None]:
    if price is None or fund_nav_t1 is None or fund_nav_t1 <= 0 or index_change_pct is None:
        return {"estimate_nav": None, "estimate_premium": None}
    fx = fx_change_pct if fx_change_pct is not None else 0.0
    estimate_nav = round(fund_nav_t1 * (1 + index_change_pct) * (1 + fx), 6)
    if estimate_nav <= 0:
        return {"estimate_nav": None, "estimate_premium": None}
    return {
        "estimate_nav": estimate_nav,
        "estimate_premium": round(price / estimate_nav - 1, 6),
    }


def classify_quality(
    *,
    nav_ok: bool,
    primary_index_ok: bool,
    fx_ok: bool,
    correlation: str,
    formula_type: str,
) -> str:
    """Grade an entry based on nav/index/fx availability + intrinsic correlation."""
    if not nav_ok or not primary_index_ok:
        return "unavailable"
    if formula_type in {"mixed", "hybrid"} or correlation == "weak":
        return "low"
    if not fx_ok:
        return "medium"
    if correlation == "medium":
        return "medium"
    return "high"


# ---------------------------------------------------------------------------
# v2: 混合口径复合指数拟合 (164906 / 160644)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompositeConfig:
    code: str
    name: str
    ref_index_symbol: str
    ref_index_name: str
    hk_kline_symbol: str
    hk_kline_name: str
    us_target_symbol: str
    us_target_name: str
    us_target_free_daily: str


COMPOSITE_CONFIGS: tuple[CompositeConfig, ...] = (
    CompositeConfig(
        code="164906",
        name="中概互联网LOF",
        ref_index_symbol="H11136.CSI",
        ref_index_name="中证海外中国互联网指数",
        hk_kline_symbol="hkHSTECH",
        hk_kline_name="恒生科技指数",
        us_target_symbol="usKWEB",
        us_target_name="KraneShares 中概互联网 ETF",
        us_target_free_daily=(
            "腾讯 usfqkline qfqday 对美股 ETF 只回最新一帧(2017 后日 K 仅返回 1 行); "
            "东财 push2his 106.KWEB 与 Yahoo v8 chart 当前断连; "
            "KWEB 免费日 K 30 日序列不可得"
        ),
    ),
    CompositeConfig(
        code="160644",
        name="港美互联网LOF",
        ref_index_symbol="H11136.CSI",
        ref_index_name="中证海外中国互联网指数",
        hk_kline_symbol="hkHSTECH",
        hk_kline_name="恒生科技指数",
        us_target_symbol="usKWEB",
        us_target_name="KraneShares 中概互联网 ETF",
        us_target_free_daily=(
            "同 164906; usKWEB 免费日 K 不可得, 回归因子使用 H11136_ref(集思录官方参考指数)+HSTECH"
        ),
    ),
)


def _extract_daily_fund_and_ref(
    hist_cells: list[dict[str, Any]],
) -> list[tuple[str, float, float]]:
    """从 detail_hists 抽取 (nav_date, fund_daily_return, official_ref_pct)。"""
    triples: list[tuple[str, float, float]] = []
    for cell in hist_cells:
        nv = to_float(cell.get("net_value"))
        dt = cell.get("net_value_dt")
        ref = to_float(cell.get("ref_increase_rt"))
        if nv is None or not dt or ref is None:
            continue
        triples.append((dt, nv, ref / 100))
    triples.sort(key=lambda t: t[0])
    daily: list[tuple[str, float, float]] = []
    for i in range(1, len(triples)):
        d, nv, ref = triples[i]
        prev_dt, prev_nv, _ = triples[i - 1]
        if d == prev_dt or prev_nv <= 0:
            continue
        daily.append((d, nv / prev_nv - 1, ref))
    return daily


def _rmse(y: list[float], y_hat: list[float]) -> float:
    n = len(y)
    if n == 0:
        return float("inf")
    total = 0.0
    for a, b in zip(y, y_hat):
        total += (a - b) ** 2
    return (total / n) ** 0.5


def fit_two_factor_ols(
    fund_returns: list[float],
    factor_a: list[float],
    factor_b: list[float],
) -> dict[str, Any] | None:
    """双因子无截距 OLS: y = w_a * a + w_b * b。闭式解。"""
    n = len(fund_returns)
    if n == 0 or n != len(factor_a) or n != len(factor_b):
        return None
    saa = sum(x * x for x in factor_a)
    sbb = sum(x * x for x in factor_b)
    sab = sum(a * b for a, b in zip(factor_a, factor_b))
    sya = sum(y * x for y, x in zip(fund_returns, factor_a))
    syb = sum(y * x for y, x in zip(fund_returns, factor_b))
    det = saa * sbb - sab * sab
    if abs(det) < 1e-18:
        return None
    w_a = (sbb * sya - sab * syb) / det
    w_b = (-sab * sya + saa * syb) / det
    predicted = [w_a * factor_a[i] + w_b * factor_b[i] for i in range(n)]
    return {"w_a": w_a, "w_b": w_b, "rmse": _rmse(fund_returns, predicted), "n": n}


def grid_search_two_factor(
    fund_returns: list[float],
    factor_a: list[float],
    factor_b: list[float],
    w_a_lo: float = 0.3,
    w_a_hi: float = 0.7,
    step: float = 0.05,
    sum_to_one: bool = True,
) -> dict[str, Any]:
    """网格搜索 w_a in [lo, hi], step; sum_to_one 时 w_b = 1 - w_a。"""
    n = len(fund_returns)
    best = {"w_a": None, "w_b": None, "rmse": float("inf")}
    trials: list[dict[str, float]] = []
    if step <= 0:
        return {"best": best, "trials": trials}
    steps = int(round((w_a_hi - w_a_lo) / step)) + 1
    for i in range(steps):
        w_a = round(w_a_lo + i * step, 4)
        w_b = round(1.0 - w_a, 4) if sum_to_one else 0.0
        predicted = [w_a * factor_a[k] + w_b * factor_b[k] for k in range(n)]
        rr = _rmse(fund_returns, predicted)
        trials.append({"w_a": w_a, "w_b": w_b, "rmse": rr})
        if rr < best["rmse"]:
            best = {"w_a": w_a, "w_b": w_b, "rmse": rr}
    return {"best": best, "trials": trials}


def classify_composite_quality(rmse: float) -> str:
    """PM v2 阈值: RMSE < 0.5% -> medium; RMSE >= 1% -> low。"""
    if rmse < 0.005:
        return "medium"
    if rmse < 0.010:
        return "medium"
    return "low"


class _Fetcher:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            timeout=10.0,
            headers=UA,
            follow_redirects=True,
            trust_env=False,
        )
        self._owns_client = client is None
        self._jisilu_cache: dict[str, dict[str, Any]] | None = None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def fetch_market_price(self, code: str) -> dict[str, Any]:
        symbol = market_symbol(code)
        try:
            resp = self._client.get(TENCENT_QUOTE_URL.format(symbols=symbol))
            resp.raise_for_status()
            parsed = parse_tencent_quote_payload(resp.text).get(symbol, {})
            parsed["ok"] = parsed.get("price") is not None
            return parsed
        except Exception as exc:
            return {"ok": False, "error": type(exc).__name__}

    def fetch_tencent_indexes(self, symbols: Iterable[str]) -> dict[str, dict[str, Any]]:
        symbols = list(symbols)
        if not symbols:
            return {}
        try:
            resp = self._client.get(TENCENT_QUOTE_URL.format(symbols=",".join(symbols)))
            resp.raise_for_status()
            return parse_tencent_index_payload(resp.text)
        except Exception:
            return {}

    def fetch_sina_gb(self, symbols: Iterable[str]) -> dict[str, dict[str, Any]]:
        symbols = list(symbols)
        if not symbols:
            return {}
        try:
            resp = self._client.get(SINA_LIST_URL.format(symbols=",".join(symbols)), headers=SINA_HEADERS)
            resp.raise_for_status()
            return parse_sina_gb_payload(resp.text)
        except Exception:
            return {}

    def fetch_sina_fx(self, symbols: Iterable[str]) -> dict[str, dict[str, Any]]:
        symbols = list(symbols)
        if not symbols:
            return {}
        try:
            resp = self._client.get(SINA_LIST_URL.format(symbols=",".join(symbols)), headers=SINA_HEADERS)
            resp.raise_for_status()
            return parse_sina_fx_payload(resp.text)
        except Exception:
            return {}

    def fetch_fundgz(self, code: str) -> dict[str, Any]:
        try:
            resp = self._client.get(FUNDGZ_URL.format(code=code) + f"?rt={int(time.time() * 1000)}")
            resp.raise_for_status()
            return parse_fundgz_payload(resp.text)
        except Exception as exc:
            return {"ok": False, "reason": type(exc).__name__}

    def fetch_jisilu_qdii(
        self,
        cookie: str | None,
        categories: tuple[str, ...] = JISILU_QDII_LIST_CATEGORIES,
    ) -> dict[str, dict[str, Any]]:
        """v2: 跨类目合并 QDII 列表。默认类目 + E 类(LOF)覆盖 501225/164824/501312 等。"""
        if self._jisilu_cache is not None:
            return self._jisilu_cache
        headers = {**UA, "Referer": JISILU_QDII_REFERER}
        if cookie:
            headers["Cookie"] = cookie
        merged: dict[str, dict[str, Any]] = {}
        source_by_code: dict[str, str] = {}
        for cat in categories:
            # E 类接口要求 /qdii_list/E (无尾斜杠), 加了尾斜杠会走到 HTML 页; 默认类目保留 /qdii_list/
            cat_clean = cat.strip("/")
            url = JISILU_QDII_LIST_URL + cat_clean if cat_clean else JISILU_QDII_LIST_URL
            params: dict[str, str] = {
                "___jsl": f"LST___t={int(time.time() * 1000)}",
                "rp": "300",
                "page": "1",
            }
            if cat == "E":
                params.update({"only_lof": "y", "only_etf": "y"})
            try:
                resp = self._client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json() or {}
                rows = data.get("rows") or []
            except Exception:
                continue
            for row in rows:
                cell = row.get("cell") or {}
                code = str(cell.get("fund_id") or "").zfill(6)
                if not code:
                    continue
                incoming = {
                    "fund_nav": to_float(cell.get("fund_nav")),
                    "nav_dt": cell.get("nav_dt") or "",
                    "name": cell.get("fund_nm") or "",
                    "index_id": cell.get("index_id") or "",
                    "index_nm": cell.get("index_nm") or "",
                    "cal_index_id": cell.get("cal_index_id") or "",
                    "cal_tips": cell.get("cal_tips") or "",
                    "ref_increase_rt": to_float(cell.get("ref_increase_rt")),
                    "us_increase_rt": to_float(cell.get("us_increase_rt")),
                    "est_val_increase_rt": to_float(cell.get("est_val_increase_rt")),
                    "nav_discount_rt": to_float(cell.get("nav_discount_rt")),
                }
                if (
                    code in merged
                    and merged[code].get("fund_nav") is not None
                    and incoming.get("fund_nav") is None
                ):
                    continue
                merged[code] = incoming
                source_by_code[code] = cat or "default"
        for code, entry in merged.items():
            entry["category_source"] = source_by_code.get(code, "default")
        self._jisilu_cache = merged
        return merged

    def fetch_detail_hists(
        self, code: str, cookie: str | None, rp: int = 60
    ) -> list[dict[str, Any]]:
        """集思录 QDII detail_hists 60 日历史;需 Cookie 才能拉全窗口。"""
        headers = {
            **UA,
            "Referer": f"https://www.jisilu.cn/data/qdii/detail/{code}",
            "X-Requested-With": "XMLHttpRequest",
        }
        if cookie:
            headers["Cookie"] = cookie
        try:
            resp = self._client.post(
                JISILU_QDII_DETAIL_HISTS_URL.format(code=code),
                data={"is_search": 1, "fund_id": code, "rp": rp},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json() or {}
            return [row.get("cell") or {} for row in (data.get("rows") or [])]
        except Exception:
            return []

    def fetch_tencent_hk_daily(self, symbol: str, limit: int = 60) -> dict[str, float]:
        """腾讯港股 hkfqkline 日 K -> {日期: 日涨跌率}"""
        try:
            resp = self._client.get(
                TENCENT_HK_KLINE_URL,
                params={"_var": "k", "param": f"{symbol},day,,,{limit},qfq"},
            )
            resp.raise_for_status()
            body = resp.text.split("=", 1)[1] if "=" in resp.text[:20] else resp.text
            data = json.loads(body)
            info = data["data"].get(symbol) or {}
            klines = info.get("day") or info.get("qfqday") or []
        except Exception:
            return {}
        out: dict[str, float] = {}
        prev_close: float | None = None
        for row in klines:
            if not row or len(row) < 3:
                continue
            date = row[0]
            close = to_float(row[2])
            if close is None:
                continue
            if prev_close is not None and prev_close > 0:
                out[date] = round(close / prev_close - 1, 6)
            prev_close = close
        return out


def _probe_candidate_availability(
    candidate: IndexCandidate,
    tencent_index_map: dict[str, dict[str, Any]],
    sina_gb_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if candidate.source == "tencent":
        data = tencent_index_map.get(candidate.symbol)
        ok = bool(data and data.get("price") is not None and data.get("change_pct") is not None)
        return {
            "symbol": candidate.symbol,
            "source": "tencent",
            "display_name": candidate.display_name,
            "cookie_required": candidate.cookie_required,
            "ok": ok,
            "change_pct": data.get("change_pct") if data else None,
            "price": data.get("price") if data else None,
            "quote_time": data.get("quote_time") if data else "",
            "correlation_note": candidate.correlation_note,
        }
    if candidate.source == "sina_gb":
        data = sina_gb_map.get(candidate.symbol)
        ok = bool(data and data.get("price") is not None and data.get("change_pct") is not None)
        return {
            "symbol": candidate.symbol,
            "source": "sina_gb",
            "display_name": candidate.display_name,
            "cookie_required": candidate.cookie_required,
            "ok": ok,
            "change_pct": data.get("change_pct") if data else None,
            "price": data.get("price") if data else None,
            "quote_time": data.get("quote_time") if data else "",
            "correlation_note": candidate.correlation_note,
        }
    return {
        "symbol": candidate.symbol,
        "source": candidate.source,
        "ok": False,
        "reason": "unsupported_source",
    }


def build_item(
    mapping: Batch13Mapping,
    *,
    price_info: dict[str, Any],
    fundgz_info: dict[str, Any],
    jisilu_row: dict[str, Any] | None,
    tencent_index_map: dict[str, dict[str, Any]],
    sina_gb_map: dict[str, dict[str, Any]],
    fx_map: dict[str, dict[str, Any]],
    cookie_present: bool,
) -> dict[str, Any]:
    nav_source = None
    fund_nav_t1: float | None = None
    nav_dt: str = ""
    jisilu_index_id = ""
    jisilu_index_nm = ""
    if jisilu_row and jisilu_row.get("fund_nav") is not None:
        fund_nav_t1 = jisilu_row["fund_nav"]
        nav_dt = jisilu_row.get("nav_dt") or ""
        nav_source = "jisilu_qdii"
        jisilu_index_id = jisilu_row.get("index_id") or ""
        jisilu_index_nm = jisilu_row.get("index_nm") or ""
    elif fundgz_info.get("ok"):
        fund_nav_t1 = fundgz_info.get("fund_nav_t1")
        nav_dt = fundgz_info.get("nav_dt") or ""
        nav_source = "fundgz"

    candidates_status = [
        _probe_candidate_availability(c, tencent_index_map, sina_gb_map)
        for c in mapping.candidates
    ]
    primary = next((c for c in candidates_status if c.get("ok")), None)
    index_change_pct = primary.get("change_pct") if primary else None
    index_symbol = primary.get("symbol") if primary else None
    index_display = primary.get("display_name") if primary else None

    fx_symbol = None
    if mapping.fx_pair == "USD/CNY":
        fx_symbol = "fx_susdcny"
    elif mapping.fx_pair == "HKD/CNY":
        fx_symbol = "fx_shkdcny"
    fx_change_pct = None
    fx_ok = False
    if fx_symbol and fx_symbol in fx_map:
        fx_change_pct = fx_map[fx_symbol].get("change_pct")
        fx_ok = fx_change_pct is not None

    estimate = calculate_estimate(
        price=price_info.get("price"),
        fund_nav_t1=fund_nav_t1,
        index_change_pct=index_change_pct,
        fx_change_pct=fx_change_pct,
    )

    quality = classify_quality(
        nav_ok=fund_nav_t1 is not None,
        primary_index_ok=primary is not None,
        fx_ok=fx_ok,
        correlation=mapping.single_index_correlation,
        formula_type=mapping.formula_type,
    )

    reasons: list[str] = []
    if not price_info.get("ok"):
        reasons.append("missing_market_price")
    if fund_nav_t1 is None:
        if jisilu_row is None:
            if cookie_present:
                reasons.append("jisilu_qdii_row_not_found_with_cookie")
            else:
                reasons.append("missing_nav_no_cookie_jisilu_truncated")
        if not fundgz_info.get("ok"):
            reasons.append(f"fundgz_{fundgz_info.get('reason', 'empty')}")
    if primary is None:
        reasons.append("no_free_index_source_available")
    if not fx_ok:
        reasons.append("fx_unavailable_default_0")
    if mapping.note:
        reasons.append(mapping.note)

    return {
        "code": mapping.code,
        "name": mapping.name,
        "asset_region": mapping.asset_region,
        "currency": mapping.currency,
        "fx_pair": mapping.fx_pair,
        "formula_type": mapping.formula_type,
        "single_index_correlation": mapping.single_index_correlation,
        "price": price_info.get("price"),
        "price_change_pct": price_info.get("change_pct"),
        "amount": price_info.get("amount"),
        "price_source": "tencent_quote",
        "fund_nav_t1": fund_nav_t1,
        "nav_dt": nav_dt,
        "nav_source": nav_source,
        "jisilu_index_id": jisilu_index_id,
        "jisilu_index_nm": jisilu_index_nm,
        "reference_index_symbol": index_symbol,
        "reference_index_display": index_display,
        "reference_index_change_pct": index_change_pct,
        "fx_symbol": fx_symbol,
        "fx_change_pct": fx_change_pct,
        "estimate_nav": estimate["estimate_nav"],
        "estimate_premium": estimate["estimate_premium"],
        "estimate_quality": quality,
        "candidates_status": candidates_status,
        "reasons": ";".join(dict.fromkeys(reasons)) if reasons else "",
    }


def build_report(items: list[dict[str, Any]], *, cookie_present: bool) -> dict[str, Any]:
    quality_counts = {q: sum(1 for it in items if it["estimate_quality"] == q)
                      for q in ("high", "medium", "low", "unavailable")}
    high_codes = [it["code"] for it in items if it["estimate_quality"] == "high"]
    recommendations = []
    for it in items:
        recommendations.append({
            "code": it["code"],
            "name": it["name"],
            "quality": it["estimate_quality"],
            "recommend_high": it["estimate_quality"] == "high",
            "reason": it["reasons"] or (
                "候选指数强相关免费源可得, 指数/汇率/净值三要素齐备"
                if it["estimate_quality"] == "high"
                else ""
            ),
        })
    return {
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "scope": (
            "QDII 13 只 LOF 参考指数免费源批量 POC; 只读; 不接主链路; "
            "不改 PRD §6 与 QDII_REFERENCE_MAPPINGS; 不写 uniCloud"
        ),
        "disclaimer": "参考指数估算, 非交易所 IOPV",
        "formula": (
            "estimate_nav = fund_nav_t1 * (1 + index_change_pct) * (1 + fx_change_pct); "
            "estimate_premium = price / estimate_nav - 1"
        ),
        "cookie_mode": "with_cookie" if cookie_present else "anonymous",
        "sample_count": len(items),
        "quality_counts": quality_counts,
        "recommended_high_codes": high_codes,
        "recommendations": recommendations,
        "source_stability": {
            "market_price": "tencent_quote 覆盖所有 13 只 A 股场内 LOF/ETF",
            "nav_t1": (
                "集思录 qdii_list 需 Cookie 才能覆盖 267 条; 匿名仅前 20 条; "
                "fundgz 对 501225 / 164906 / 164824 / 160125 常返回空 jsonpgz()"
            ),
            "reference_index_us_broad": "usINX / usNDX / usIXIC / usDJI 腾讯免费实时可得",
            "reference_index_us_sector_etf": (
                "美股行业指数(SPSIBI / S5HLTH / S5INFT)免费源不可得; 用 SPDR/iShares ETF 代理: "
                "usXBI / usXLV / usXLK / usXLY / usVNQ / usSOXX / usIYW / usKWEB / usINDA"
            ),
            "reference_index_hk": "hkHSI / hkHSCEI / hkHSTECH 腾讯免费实时可得",
            "fx": "新浪 fx_susdcny / fx_shkdcny 稳定可得; 涨跌幅字段为百分比数",
        },
        "ccr": "not_triggered_readonly_poc_no_prd6_change",
        "items": items,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    dot = chr(0x00B7)
    lines.append("# QDII 13 只 LOF 参考指数免费源批量 POC")
    lines.append("")
    lines.append(f"- 探测时间: {report['ts']}")
    lines.append(f"- 口径: {report['disclaimer']} (only reference-index estimate, NOT exchange IOPV)")
    lines.append(f"- 范围: {report['scope']}")
    lines.append(f"- Cookie 模式: {report['cookie_mode']}")
    lines.append(f"- 公式: `{report['formula']}`")
    lines.append(f"- 样本量: {report['sample_count']}")
    lines.append(f"- 质量统计: {report['quality_counts']}")
    lines.append(f"- 推荐 high 准入清单: {report['recommended_high_codes']}")
    lines.append(f"- CCR: {report['ccr']}")
    lines.append("")
    lines.append("## 样本明细")
    lines.append("")
    lines.append(
        "| code | name | region | corr | price | price_chg | fund_nav_t1 | nav_dt | nav_src | ref_idx | idx_chg | fx | fx_chg | est_nav | est_prem | quality | reasons |"
    )
    lines.append(
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
    )
    for it in report["items"]:
        lines.append(
            f"| {it['code']} | {it['name']} | {it['asset_region']} | {it['single_index_correlation']} | "
            f"{it.get('price')} | {it.get('price_change_pct')} | {it.get('fund_nav_t1')} | {it.get('nav_dt')} | "
            f"{it.get('nav_source')} | {it.get('reference_index_symbol') or '-'} | {it.get('reference_index_change_pct')} | "
            f"{it.get('fx_symbol') or '-'} | {it.get('fx_change_pct')} | {it.get('estimate_nav')} | "
            f"{it.get('estimate_premium')} | {it['estimate_quality']} | {it.get('reasons')} |"
        )
    lines.append("")
    lines.append("## 每只候选指数源可得性")
    lines.append("")
    for it in report["items"]:
        lines.append(f"### {it['code']} {it['name']}")
        for c in it["candidates_status"]:
            flag = "OK" if c.get("ok") else "MISS"
            note = c.get("correlation_note", "")
            note_part = f" {dot} {note}" if note else ""
            lines.append(
                f"- [{flag}] {c.get('symbol')} ({c.get('source')}): change_pct={c.get('change_pct')}{note_part}"
            )
        lines.append("")
    lines.append("## 准入建议")
    lines.append("")
    for rec in report["recommendations"]:
        badge = "high" if rec["recommend_high"] else rec["quality"]
        lines.append(f"- {rec['code']} {rec['name']}: {badge} {dot} {rec['reason']}")
    lines.append("")
    if report.get("anonymous_summary") and report.get("cookie_summary"):
        lines.append("## 匿名 vs Cookie 对比")
        lines.append("")
        anon = report["anonymous_summary"]
        cook = report["cookie_summary"]
        lines.append(f"- 匿名模式质量: {anon['quality_counts']}")
        lines.append(f"- 匿名模式 high 清单: {anon['recommended_high_codes']}")
        lines.append(f"- Cookie 模式质量: {cook['quality_counts']}")
        lines.append(f"- Cookie 模式 high 清单: {cook['recommended_high_codes']}")
        added = [c for c in cook["recommended_high_codes"] if c not in anon["recommended_high_codes"]]
        removed = [c for c in anon["recommended_high_codes"] if c not in cook["recommended_high_codes"]]
        lines.append(f"- Cookie 相对匿名新增 high: {added}")
        lines.append(f"- Cookie 相对匿名减少 high: {removed}")
        lines.append("")
    elif report.get("anonymous_summary"):
        lines.append("## 匿名模式摘要")
        lines.append("")
        anon = report["anonymous_summary"]
        lines.append(f"- 匿名模式质量: {anon['quality_counts']}")
        lines.append(f"- 匿名模式 high 清单: {anon['recommended_high_codes']}")
        lines.append("")
    lines.append("## 数据源稳定性判断")
    lines.append("")
    for key, value in report["source_stability"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines) + "\n"


def run_composite_fitting(
    fetcher: "_Fetcher",
    cookie: str | None,
    configs: tuple[CompositeConfig, ...] = COMPOSITE_CONFIGS,
) -> list[dict[str, Any]]:
    """对每只 mixed-exposure 代码, 拉集思录 detail_hists + 腾讯 HSTECH 日 K, 做双因子回归。"""
    hstech = fetcher.fetch_tencent_hk_daily("hkHSTECH", limit=60)
    results: list[dict[str, Any]] = []
    for cfg in configs:
        rows = fetcher.fetch_detail_hists(cfg.code, cookie, rp=60)
        daily = _extract_daily_fund_and_ref(rows)
        aligned_dates: list[str] = []
        fund_returns: list[float] = []
        ref_returns: list[float] = []
        hs_returns: list[float] = []
        for dt, r_fund, r_ref in daily:
            if dt in hstech:
                aligned_dates.append(dt)
                fund_returns.append(r_fund)
                ref_returns.append(r_ref)
                hs_returns.append(hstech[dt])
        n = len(fund_returns)
        rmse_ref_only = _rmse(fund_returns, ref_returns) if n else float("inf")
        rmse_hs_only = _rmse(fund_returns, hs_returns) if n else float("inf")
        ols = fit_two_factor_ols(fund_returns, ref_returns, hs_returns)
        grid = grid_search_two_factor(fund_returns, ref_returns, hs_returns)
        best_rmse = grid["best"]["rmse"] if grid.get("best") else float("inf")
        composite_quality = classify_composite_quality(best_rmse) if n else "unavailable"
        results.append({
            "code": cfg.code,
            "name": cfg.name,
            "ref_index_symbol": cfg.ref_index_symbol,
            "ref_index_name": cfg.ref_index_name,
            "hk_kline_symbol": cfg.hk_kline_symbol,
            "hk_kline_name": cfg.hk_kline_name,
            "us_target_symbol": cfg.us_target_symbol,
            "us_target_name": cfg.us_target_name,
            "us_target_free_daily": cfg.us_target_free_daily,
            "aligned_sample_size": n,
            "sample_date_range": (
                [aligned_dates[0], aligned_dates[-1]] if aligned_dates else []
            ),
            "rmse_ref_only": round(rmse_ref_only, 6) if n else None,
            "rmse_hstech_only": round(rmse_hs_only, 6) if n else None,
            "ols": (
                {
                    "w_ref": round(ols["w_a"], 6),
                    "w_hs": round(ols["w_b"], 6),
                    "rmse": round(ols["rmse"], 6),
                    "n": ols["n"],
                }
                if ols
                else None
            ),
            "grid": {
                "search_space": "w_ref in [0.3, 0.7] step 0.05; w_hs = 1 - w_ref",
                "best": (
                    {
                        "w_ref": grid["best"]["w_a"],
                        "w_hs": grid["best"]["w_b"],
                        "rmse": (
                            round(grid["best"]["rmse"], 6)
                            if grid["best"]["rmse"] != float("inf")
                            else None
                        ),
                    }
                    if grid.get("best")
                    else None
                ),
                "trials": [
                    {
                        "w_ref": t["w_a"],
                        "w_hs": t["w_b"],
                        "rmse": (
                            round(t["rmse"], 6)
                            if t["rmse"] != float("inf")
                            else None
                        ),
                    }
                    for t in grid.get("trials", [])
                ],
            },
            "composite_quality": composite_quality,
        })
    return results


V1_QUALITY_BASELINE: dict[str, str] = {
    "501225": "unavailable",
    "161127": "high",
    "161126": "high",
    "161130": "high",
    "161125": "high",
    "164906": "low",
    "161128": "high",
    "160140": "medium",
    "164824": "unavailable",
    "162415": "medium",
    "160125": "high",
    "501312": "high",
    "160644": "low",
}


def build_report_v2(
    base: dict[str, Any],
    composite_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """在 v1 报告基础上追加: E 类补测、复合拟合、v1 vs v2 质量矩阵、结构性建议。"""
    quality_map = {it["code"]: it["estimate_quality"] for it in base["items"]}
    nav_source_map = {it["code"]: it.get("nav_source") for it in base["items"]}
    e_class_recovered = [
        code for code in ("501225", "164824", "501312")
        if quality_map.get(code) not in (None, "unavailable")
    ]
    high_codes_v2 = [code for code, q in quality_map.items() if q == "high"]

    matrix = []
    for code, q_v1 in V1_QUALITY_BASELINE.items():
        q_v2 = quality_map.get(code, "unavailable")
        if q_v2 == q_v1:
            delta = "unchanged"
        elif q_v1 == "unavailable" and q_v2 != "unavailable":
            delta = "upgraded"
        else:
            delta = "changed"
        matrix.append({
            "code": code,
            "v1_quality": q_v1,
            "v2_quality": q_v2,
            "delta": delta,
            "nav_source_v2": nav_source_map.get(code),
        })

    report = dict(base)
    report["version"] = "v2"
    report["scope"] = (
        "QDII 13 只 LOF 参考指数免费源批量 POC v2; 只读; 不接主链路; "
        "不改 PRD §6 与 QDII_REFERENCE_MAPPINGS; 不写 uniCloud; "
        "v2 补测: E 类接口 + 混合口径复合指数拟合"
    )
    report["e_class_probe"] = {
        "endpoint": "https://www.jisilu.cn/data/qdii/qdii_list/E?only_lof=y&only_etf=y&rp=300",
        "note": (
            "v1 只抓默认类目, 501225 / 164824 / 501312 未命中; v2 追加 category=E "
            "并按 fund_nav 存在性优先合并, 补齐 LOF 类 QDII 净值"
        ),
        "recovered_codes": e_class_recovered,
    }
    report["composite_fitting"] = {
        "method": (
            "两因子 OLS (无截距): y_fund_daily = w_ref * ref_official_daily + w_hs * hkHSTECH_daily; "
            "同时网格搜索 w_ref ∈ [0.3, 0.7] step 0.05, w_hs = 1 - w_ref"
        ),
        "factor_ref_source": (
            "集思录 detail_hists ref_increase_rt (官方参考指数日涨跌%); "
            "免费替代 usKWEB 日 K 不可得的说明见 free_source_notes"
        ),
        "factor_hs_source": "腾讯 hkfqkline hkHSTECH 60 日 qfq 日 K",
        "quality_thresholds": (
            "RMSE < 0.5% -> medium (仅在复合优于任一单因子时才提升); "
            "RMSE >= 1.0% -> 保持 low"
        ),
        "results": composite_results,
        "free_source_notes": [
            (
                "usKWEB (KraneShares 中概互联网 ETF) 免费日 K 30 日序列不可得: "
                "腾讯 usfqkline qfqday 对美股 ETF 仅回传最新 1 帧; "
                "东财 push2his 106.KWEB 与 Yahoo v8 chart 当前断连"
            ),
            "港股 hkHSTECH 通过腾讯 hkfqkline 可稳定拿 60 日 qfq 日 K",
            "H11136 官方参考指数日涨跌% 通过集思录 detail_hists 可得, 但需 Cookie",
        ],
    }
    report["quality_matrix_v1_vs_v2"] = matrix
    report["recommended_high_codes_v2"] = high_codes_v2
    report["structural_recommendation"] = {
        "field": "qdii_reference_index_weights",
        "shape": "list[{symbol: str, weight: number}]",
        "purpose": (
            "支持 mixed-exposure QDII (如 164906 / 160644) 用两个以上参考指数加权拟合 estimate_nav; "
            "PRD 1.6 只支持单指数, 引入该结构属于结构性变更"
        ),
        "ccr_required": True,
        "ccr_target": "PRD 1.6.2",
        "poc_impact": "本轮不实装, 仅在报告中建议",
    }
    report["ccr"] = (
        "not_triggered_readonly_poc; 若后续把 qdii_reference_index_weights 或 "
        "E 类补测结论并入主链路, 需另立 PRD 1.6.2 CCR"
    )
    return report


def render_markdown_v2(report: dict[str, Any]) -> str:
    dot = chr(0x00B7)
    lines: list[str] = []
    lines.append("# QDII 13 只 LOF 参考指数免费源批量 POC v2")
    lines.append("")
    lines.append(f"- 探测时间: {report['ts']}")
    lines.append(
        f"- 口径: {report['disclaimer']} (only reference-index estimate, NOT exchange IOPV)"
    )
    lines.append(f"- 范围: {report['scope']}")
    lines.append(f"- Cookie 模式: {report['cookie_mode']}")
    lines.append(f"- 公式: `{report['formula']}`")
    lines.append(f"- 样本量: {report['sample_count']}")
    lines.append(f"- 质量统计: {report['quality_counts']}")
    lines.append(f"- v2 推荐 high 准入清单: {report['recommended_high_codes_v2']}")
    lines.append(f"- CCR: {report['ccr']}")
    lines.append("")
    lines.append("## 任务一 - E 类接口补测")
    lines.append("")
    lines.append(f"- 接口: `{report['e_class_probe']['endpoint']}`")
    lines.append(f"- 说明: {report['e_class_probe']['note']}")
    lines.append(
        f"- 通过 E 类恢复的代码: {report['e_class_probe']['recovered_codes']}"
    )
    lines.append("")
    lines.append("## 任务二 - 混合口径复合指数拟合")
    lines.append("")
    lines.append(f"- 方法: {report['composite_fitting']['method']}")
    lines.append(f"- 因子 ref 源: {report['composite_fitting']['factor_ref_source']}")
    lines.append(f"- 因子 HSTECH 源: {report['composite_fitting']['factor_hs_source']}")
    lines.append(f"- 阈值: {report['composite_fitting']['quality_thresholds']}")
    lines.append("")
    for cr in report["composite_fitting"]["results"]:
        lines.append(f"### {cr['code']} {cr['name']}")
        lines.append(
            f"- 样本 (对齐后交易日数): {cr['aligned_sample_size']}; 日期段: {cr['sample_date_range']}"
        )
        lines.append(
            f"- 单因子 rmse: ref_only={cr['rmse_ref_only']}, hstech_only={cr['rmse_hstech_only']}"
        )
        if cr.get("ols"):
            o = cr["ols"]
            lines.append(
                f"- OLS 最优: w_ref={o['w_ref']}, w_hs={o['w_hs']}, rmse={o['rmse']} (n={o['n']})"
            )
        if cr.get("grid", {}).get("best"):
            g = cr["grid"]["best"]
            lines.append(
                f"- 网格最优 (w_ref∈[0.3,0.7]): w_ref={g['w_ref']}, w_hs={g['w_hs']}, rmse={g['rmse']}"
            )
        lines.append(f"- 复合质量判定: {cr['composite_quality']}")
        lines.append(f"- 备注: {cr['us_target_free_daily']}")
        lines.append("")
    lines.append("## 免费源可得性备注")
    for note in report["composite_fitting"]["free_source_notes"]:
        lines.append(f"- {note}")
    lines.append("")
    lines.append("## 13 只质量矩阵 v1 vs v2")
    lines.append("")
    lines.append("| code | v1 | v2 | delta | nav_source_v2 |")
    lines.append("|---|---|---|---|---|")
    for row in report["quality_matrix_v1_vs_v2"]:
        lines.append(
            f"| {row['code']} | {row['v1_quality']} | {row['v2_quality']} | {row['delta']} | {row['nav_source_v2']} |"
        )
    lines.append("")
    lines.append("## 样本明细 (v2 单指数路径)")
    lines.append("")
    lines.append(
        "| code | name | corr | price | price_chg | fund_nav_t1 | nav_dt | nav_src | "
        "ref_idx | idx_chg | fx | fx_chg | est_nav | est_prem | quality |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for it in report["items"]:
        lines.append(
            f"| {it['code']} | {it['name']} | {it['single_index_correlation']} | "
            f"{it.get('price')} | {it.get('price_change_pct')} | {it.get('fund_nav_t1')} | "
            f"{it.get('nav_dt')} | {it.get('nav_source')} | "
            f"{it.get('reference_index_symbol') or '-'} | {it.get('reference_index_change_pct')} | "
            f"{it.get('fx_symbol') or '-'} | {it.get('fx_change_pct')} | "
            f"{it.get('estimate_nav')} | {it.get('estimate_premium')} | {it['estimate_quality']} |"
        )
    lines.append("")
    lines.append("## 结构性建议 (报告级, 不实装)")
    sr = report["structural_recommendation"]
    lines.append(f"- 建议字段: `{sr['field']}` {dot} 形状: `{sr['shape']}`")
    lines.append(f"- 用途: {sr['purpose']}")
    lines.append(
        f"- CCR: 需 {sr['ccr_target']} {dot} required={sr['ccr_required']}"
    )
    lines.append(f"- 本轮 POC 影响: {sr['poc_impact']}")
    lines.append("")
    if report.get("anonymous_summary") and report.get("cookie_summary"):
        lines.append("## 匿名 vs Cookie 对比")
        lines.append("")
        anon = report["anonymous_summary"]
        cook = report["cookie_summary"]
        lines.append(f"- 匿名模式质量: {anon['quality_counts']}")
        lines.append(f"- 匿名模式 high 清单: {anon['recommended_high_codes']}")
        lines.append(f"- Cookie 模式质量: {cook['quality_counts']}")
        lines.append(f"- Cookie 模式 high 清单: {cook['recommended_high_codes']}")
        lines.append("")
    lines.append("## 数据源稳定性判断")
    for key, value in report["source_stability"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return chr(10).join(lines) + chr(10)


def write_reports_v2(report: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "backend-qdii-batch13-probe-v2.json"
    md_path = output_dir / "backend-qdii-batch13-probe-v2.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8"
    )
    md_path.write_text(render_markdown_v2(report), encoding="utf-8")
    return {"json": json_path, "md": md_path}


def write_reports(report: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "backend-qdii-batch13-probe-v1.json"
    md_path = output_dir / "backend-qdii-batch13-probe-v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "md": md_path}


def run_probe(
    fetcher: _Fetcher | None = None,
    mappings: tuple[Batch13Mapping, ...] = BATCH13_MAPPINGS,
    cookie_override: str | None = None,
    force_anonymous: bool = False,
) -> dict[str, Any]:
    if force_anonymous:
        cookie = None
    elif cookie_override is not None:
        cookie = cookie_override.strip() or None
    else:
        cookie = os.environ.get("JISILU_COOKIE", "").strip() or None
    owns_fetcher = fetcher is None
    fetcher = fetcher or _Fetcher()
    try:
        jisilu_map = fetcher.fetch_jisilu_qdii(cookie)

        tencent_symbols: set[str] = set()
        sina_gb_symbols: set[str] = set()
        for m in mappings:
            for c in m.candidates:
                if c.source == "tencent":
                    tencent_symbols.add(c.symbol)
                elif c.source == "sina_gb":
                    sina_gb_symbols.add(c.symbol)
        tencent_index_map = fetcher.fetch_tencent_indexes(sorted(tencent_symbols))
        sina_gb_map = fetcher.fetch_sina_gb(sorted(sina_gb_symbols))
        fx_map = fetcher.fetch_sina_fx(["fx_susdcny", "fx_shkdcny"])

        items = []
        for m in mappings:
            price_info = fetcher.fetch_market_price(m.code)
            fundgz_info = fetcher.fetch_fundgz(m.code)
            items.append(
                build_item(
                    m,
                    price_info=price_info,
                    fundgz_info=fundgz_info,
                    jisilu_row=jisilu_map.get(m.code),
                    tencent_index_map=tencent_index_map,
                    sina_gb_map=sina_gb_map,
                    fx_map=fx_map,
                    cookie_present=cookie is not None,
                )
            )
        return build_report(items, cookie_present=cookie is not None)
    finally:
        if owns_fetcher:
            fetcher.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="QDII 13 batch reference-index free-source probe (read-only POC)"
    )
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--anonymous-only", action="store_true",
                        help="skip cookie run even if JISILU_COOKIE is set")
    parser.add_argument("--v2", action="store_true",
                        help="emit v2 report (E-category + composite fitting)")
    args = parser.parse_args(argv)

    env_cookie = os.environ.get("JISILU_COOKIE", "").strip() or None
    anon_report = run_probe(force_anonymous=True)
    cookie_report = None
    if env_cookie and not args.anonymous_only:
        cookie_report = run_probe(cookie_override=env_cookie)

    primary = cookie_report or anon_report
    combined = {
        **primary,
        "anonymous_summary": {
            "cookie_mode": anon_report["cookie_mode"],
            "quality_counts": anon_report["quality_counts"],
            "recommended_high_codes": anon_report["recommended_high_codes"],
            "nav_source_by_code": {it["code"]: it["nav_source"] for it in anon_report["items"]},
            "estimate_premium_by_code": {it["code"]: it["estimate_premium"] for it in anon_report["items"]},
            "quality_by_code": {it["code"]: it["estimate_quality"] for it in anon_report["items"]},
        },
    }
    if cookie_report:
        combined["cookie_summary"] = {
            "cookie_mode": cookie_report["cookie_mode"],
            "quality_counts": cookie_report["quality_counts"],
            "recommended_high_codes": cookie_report["recommended_high_codes"],
            "nav_source_by_code": {it["code"]: it["nav_source"] for it in cookie_report["items"]},
            "estimate_premium_by_code": {it["code"]: it["estimate_premium"] for it in cookie_report["items"]},
            "quality_by_code": {it["code"]: it["estimate_quality"] for it in cookie_report["items"]},
        }

    if args.v2:
        fetcher_v2 = _Fetcher()
        try:
            composite_results = run_composite_fitting(fetcher_v2, env_cookie)
        finally:
            fetcher_v2.close()
        combined = build_report_v2(combined, composite_results)
        files = write_reports_v2(combined, args.output_dir)
        print(
            f"[{combined['ts']}] v2 cookie_mode={combined['cookie_mode']} "
            f"quality={combined['quality_counts']} high_v2={combined['recommended_high_codes_v2']} "
            f"-> {files['json']}"
        )
    else:
        files = write_reports(combined, args.output_dir)
        print(
            f"[{combined['ts']}] cookie_mode={combined['cookie_mode']} "
            f"quality={combined['quality_counts']} -> {files['json']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
