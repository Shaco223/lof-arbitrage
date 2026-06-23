# Real daily history sources for LOF sedimentation (PRD M3.9).
#
# Two free sources, aligned by trading date:
#   - close_price: eastmoney daily kline (push2his, klt=101) -> primary;
#                  tencent daily kline (web.ifzq.gtimg.cn) -> backup.
#   - official_nav: ttjj historical NAV (LSJZ, api.fund.eastmoney.com/f10/lsjz).
#
# Read-only, free sources only. Does NOT touch the realtime main chain.
from __future__ import annotations

import json
import time
from typing import Any

import httpx

UA = {"User-Agent": "Mozilla/5.0"}
LSJZ_PAGE = 20


def eastmoney_secid(code: str) -> str:
    market = "1" if code.startswith(("50", "51", "52")) else "0"
    return f"{market}.{code}"


def tencent_symbol(code: str) -> str:
    return f"sh{code}" if code.startswith(("50", "51", "52")) else f"sz{code}"


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", " "):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_eastmoney_kline(text: str) -> dict[str, float]:
    # klines like "2026-06-22,0.527" with fields2=f51(date),f53(close).
    data = (json.loads(text) or {}).get("data") or {}
    out: dict[str, float] = {}
    for line in data.get("klines") or []:
        parts = str(line).split(",")
        if len(parts) < 2:
            continue
        date = parts[0].strip()
        close = to_float(parts[1])
        if date and close is not None:
            out[date] = close
    return out


def parse_tencent_kline(symbol: str, text: str) -> dict[str, float]:
    # rows like [date, open, close, high, low, volume].
    payload = json.loads(text)
    node = ((payload.get("data") or {}).get(symbol) or {})
    rows = node.get("qfqday") or node.get("day") or []
    out: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, list) or len(row) < 3:
            continue
        date = str(row[0]).strip()
        close = to_float(row[2])
        if date and close is not None:
            out[date] = close
    return out


def parse_lsjz(text: str) -> dict[str, float]:
    # LSJZList items: FSRQ(date), DWJZ(unit nav).
    payload = json.loads(text)
    items = (((payload or {}).get("Data") or {}).get("LSJZList")) or []
    out: dict[str, float] = {}
    for item in items:
        date = str(item.get("FSRQ") or "").strip()
        nav = to_float(item.get("DWJZ"))
        if date and nav is not None:
            out[date] = nav
    return out


class HistoryClient:
    def __init__(self, timeout: float = 10.0, retries: int = 3) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            headers=UA,
            follow_redirects=True,
            trust_env=False,
        )
        self._retries = max(1, retries)

    def close(self) -> None:
        self._client.close()

    def _get_with_retry(self, url: str, headers: dict[str, str] | None = None):
        last_exc: Exception | None = None
        for _ in range(self._retries):
            try:
                response = self._client.get(url, headers=headers)
                response.raise_for_status()
                return response
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                last_exc = exc
                time.sleep(0.4)
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("unreachable")

    def fetch_close_prices(self, code: str, limit: int = 60) -> dict[str, Any]:
        # Primary: eastmoney push2his daily kline. Backup: tencent daily kline.
        secid = eastmoney_secid(code)
        attempts: list[dict[str, Any]] = []
        start = time.perf_counter()
        try:
            url = (
                f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}"
                f"&fields1=f1&fields2=f51,f53&klt=101&fqt=1&beg=0&end=20500101&lmt={limit}"
            )
            response = self._get_with_retry(url)
            closes = parse_eastmoney_kline(response.text)
            if closes:
                attempts.append({"source": "eastmoney_kline", "hit": True})
                return {"source": "eastmoney_kline", "closes": closes, "attempts": attempts,
                        "elapsed_ms": int((time.perf_counter() - start) * 1000)}
            attempts.append({"source": "eastmoney_kline", "error": "empty"})
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            attempts.append({"source": "eastmoney_kline", "error": type(exc).__name__})

        symbol = tencent_symbol(code)
        try:
            url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,{limit},qfq"
            response = self._get_with_retry(url)
            closes = parse_tencent_kline(symbol, response.text)
            if closes:
                attempts.append({"source": "tencent_kline", "hit": True})
                return {"source": "tencent_kline", "closes": closes, "attempts": attempts,
                        "elapsed_ms": int((time.perf_counter() - start) * 1000)}
            attempts.append({"source": "tencent_kline", "error": "empty"})
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            attempts.append({"source": "tencent_kline", "error": type(exc).__name__})

        return {"source": "", "closes": {}, "attempts": attempts,
                "elapsed_ms": int((time.perf_counter() - start) * 1000), "error": "close_all_sources_failed"}

    def fetch_official_navs(self, code: str, page_size: int = 60) -> dict[str, Any]:
        # ttjj LSJZ caps each page at 20 rows regardless of pageSize, so paginate
        # until we collect enough trading-day NAVs (target ~ page_size).
        start = time.perf_counter()
        navs: dict[str, float] = {}
        pages = max(1, (page_size + LSJZ_PAGE - 1) // LSJZ_PAGE)
        last_error = ""
        for page_index in range(1, pages + 1):
            try:
                url = (
                    f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={code}"
                    f"&pageIndex={page_index}&pageSize={LSJZ_PAGE}"
                )
                response = self._get_with_retry(url, headers={"Referer": "https://fundf10.eastmoney.com/"})
                page_navs = parse_lsjz(response.text)
                if not page_navs:
                    last_error = "lsjz_empty" if not navs else last_error
                    break
                navs.update(page_navs)
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                last_error = type(exc).__name__
                break
        return {"source": "ttjj_lsjz", "navs": navs,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": "" if navs else (last_error or "lsjz_empty")}
