from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class TimedSourceValue:
    source: str
    elapsed_ms: int
    value: dict[str, Any]
    error: str = ""


POC_CODES = ["161725", "161005", "160706", "160632", "501203"]


def _is_blocked(env_name: str) -> bool:
    value = os.environ.get(env_name, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


class RealTimePocClient:
    def __init__(self, timeout: float = 5.0) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
            trust_env=False,
        )

    def close(self) -> None:
        self._client.close()

    def fetch_code_payload(self, code: str) -> dict[str, Any]:
        return {
            "price": self.fetch_market_price(code),
            "nav": self.fetch_estimated_nav(code),
        }

    def fetch_market_price(self, code: str) -> dict[str, Any]:
        result, _attempts = self._attempt_market_price(code)
        return result

    def fetch_market_price_detailed(self, code: str) -> dict[str, Any]:
        """Same as :meth:`fetch_market_price` but also exposes per-source attempts."""
        result, attempts = self._attempt_market_price(code)
        result = dict(result)
        result["attempts"] = attempts
        return result

    def _attempt_market_price(self, code: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        attempts: list[dict[str, Any]] = []
        if _is_blocked("LOF_POC_BLOCK_PRICE"):
            blocked_sources = ["tencent_quote", "eastmoney_kline", "eastmoney_push2", "sina"]
            for source in blocked_sources:
                attempts.append({"source": source, "elapsed_ms": 0, "error": "BlockedByEnv"})
            return (
                {
                    "source": ",".join(blocked_sources),
                    "elapsed_ms": 0,
                    "error": ";".join(f"{s}_BlockedByEnv" for s in blocked_sources),
                },
                attempts,
            )

        elapsed_ms = 0
        errors: list[str] = []

        symbol = market_symbol(code)
        secid = eastmoney_secid(code)

        sources = [
            ("tencent_quote", lambda: self._client.get(f"https://qt.gtimg.cn/q={symbol}"), lambda r: parse_tencent_quote_payload(r.text)),
            (
                "eastmoney_kline",
                lambda: self._client.get(
                    f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1&fields2=f51,f52&klt=1&fqt=1&beg=0&end=20500101&lmt=1"
                ),
                lambda r: parse_eastmoney_kline_payload(r.text),
            ),
            (
                "eastmoney_push2",
                lambda: self._client.get(
                    f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f57,f58,f60"
                ),
                lambda r: parse_eastmoney_push2_payload(r.text),
            ),
            ("sina", lambda: self._client.get(f"https://hq.sinajs.cn/list={symbol}"), lambda r: parse_sina_payload(symbol, r.text)),
        ]

        for source_name, fetcher_fn, parser_fn in sources:
            start = time.perf_counter()
            try:
                response = fetcher_fn()
                step_ms = elapsed_since_ms(start)
                elapsed_ms += step_ms
                response.raise_for_status()
                payload = parser_fn(response)
                payload.update({"source": source_name, "elapsed_ms": elapsed_ms})
                attempts.append({"source": source_name, "elapsed_ms": step_ms, "hit": True})
                return payload, attempts
            except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
                step_ms = elapsed_since_ms(start)
                elapsed_ms += step_ms
                err_label = type(exc).__name__
                errors.append(f"{source_name}_{err_label}")
                attempts.append({"source": source_name, "elapsed_ms": step_ms, "error": err_label})

        return (
            {
                "source": "tencent_quote,eastmoney_kline,eastmoney_push2,sina",
                "elapsed_ms": elapsed_ms,
                "error": ";".join(errors),
            },
            attempts,
        )

    def fetch_estimated_nav(self, code: str) -> dict[str, Any]:
        result, _attempts = self._attempt_estimated_nav(code)
        return result

    def fetch_estimated_nav_detailed(self, code: str) -> dict[str, Any]:
        result, attempts = self._attempt_estimated_nav(code)
        result = dict(result)
        result["attempts"] = attempts
        return result

    def _attempt_estimated_nav(self, code: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        attempts: list[dict[str, Any]] = []
        if _is_blocked("LOF_POC_BLOCK_NAV"):
            attempts.append({"source": "fundgz", "elapsed_ms": 0, "error": "BlockedByEnv"})
            return ({"source": "fundgz", "elapsed_ms": 0, "error": "nav_BlockedByEnv"}, attempts)

        start = time.perf_counter()
        try:
            response = self._client.get(f"https://fundgz.1234567.com.cn/js/{code}.js?rt={int(time.time() * 1000)}")
            elapsed_ms = elapsed_since_ms(start)
            response.raise_for_status()
            payload = parse_fundgz_payload(response.text)
            payload.update({"source": "fundgz", "elapsed_ms": elapsed_ms})
            attempts.append({"source": "fundgz", "elapsed_ms": elapsed_ms, "hit": True})
            return payload, attempts
        except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
            elapsed_ms = elapsed_since_ms(start)
            err_label = type(exc).__name__
            attempts.append({"source": "fundgz", "elapsed_ms": elapsed_ms, "error": err_label})
            return ({"source": "fundgz", "elapsed_ms": elapsed_ms, "error": f"nav_{err_label}"}, attempts)


def market_symbol(code: str) -> str:
    return f"sh{code}" if code.startswith(("50", "51", "52")) else f"sz{code}"


def eastmoney_secid(code: str) -> str:
    market = "1" if code.startswith(("50", "51", "52")) else "0"
    return f"{market}.{code}"



def parse_tencent_quote_payload(text: str) -> dict[str, Any]:
    if '=\"' not in text:
        raise ValueError("missing_tencent_payload")
    payload = text.split('="', 1)[1].rsplit('"', 1)[0]
    fields = payload.split("~")
    if len(fields) < 5:
        raise ValueError("missing_tencent_fields")
    price = to_float(fields[3])
    previous_close = to_float(fields[4])
    if price is None or price <= 0:
        raise ValueError("missing_market_price")
    # field[37] is turnover amount (in 10k CNY); absent on some quotes -> null.
    volume_amount = to_float(fields[37]) if len(fields) > 37 else None
    return {"symbol": fields[2], "name": fields[1], "price": price, "previous_close": previous_close, "volume_amount": volume_amount}

def parse_sina_payload(symbol: str, text: str) -> dict[str, Any]:
    if '=\"' not in text:
        raise ValueError("missing_sina_payload")
    payload = text.split('="', 1)[1].rsplit('"', 1)[0]
    fields = payload.split(',')
    if len(fields) < 4 or not fields[0]:
        raise ValueError("missing_sina_fields")
    price = to_float(fields[3])
    previous_close = to_float(fields[2])
    if price is None or price <= 0:
        raise ValueError("missing_market_price")
    return {"symbol": symbol, "name": fields[0], "price": price, "previous_close": previous_close}


def parse_eastmoney_push2_payload(text: str) -> dict[str, Any]:
    raw = json.loads(text)
    data = raw.get("data") or {}
    price = eastmoney_price(data.get("f43"))
    previous_close = eastmoney_price(data.get("f60"))
    if price is None or price <= 0:
        raise ValueError("missing_market_price")
    return {"symbol": str(data.get("f57") or ""), "name": data.get("f58") or "", "price": price, "previous_close": previous_close}


def parse_eastmoney_kline_payload(text: str) -> dict[str, Any]:
    raw = json.loads(text)
    data = raw.get("data") or {}
    klines = data.get("klines") or []
    if not klines:
        raise ValueError("missing_kline")
    latest = str(klines[-1]).split(",")
    if len(latest) < 2:
        raise ValueError("missing_kline_price")
    price = to_float(latest[1])
    if price is None or price <= 0:
        raise ValueError("missing_market_price")
    symbol = str(data.get("code") or "")
    return {"symbol": symbol, "name": symbol, "price": price, "previous_close": None}


def parse_fundgz_payload(text: str) -> dict[str, Any]:
    match = re.search(r"jsonpgz\((.*)\);?", text.strip())
    if not match:
        raise ValueError("missing_fundgz_payload")
    raw = json.loads(match.group(1))
    iopv = to_float(raw.get("gsz"))
    nav = to_float(raw.get("dwjz"))
    if iopv is None or iopv <= 0:
        raise ValueError("missing_estimated_nav")
    return {
        "name": raw.get("name") or "",
        "iopv": iopv,
        "nav": nav,
        "nav_date": raw.get("jzrq") or "",
        "estimate_time": raw.get("gztime") or "",
    }


def eastmoney_price(value: Any) -> float | None:
    number = to_float(value)
    if number is None:
        return None
    return round(number / 1000, 4)


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def elapsed_since_ms(start: float) -> int:
    return max(0, int(round((time.perf_counter() - start) * 1000)))
