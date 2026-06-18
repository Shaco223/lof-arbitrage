from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class MarketQuote:
    code: str
    name: str
    price: float
    previous_close: float | None = None
    source: str = "sina"


class SinaMarketClient:
    def __init__(self, timeout: float = 10.0) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
            trust_env=False,
        )

    def close(self) -> None:
        self._client.close()

    def fetch_quote(self, symbol: str) -> MarketQuote | None:
        response = self._client.get(f"https://hq.sinajs.cn/list={symbol}")
        response.raise_for_status()
        return parse_sina_quote(symbol, response.text)


def parse_sina_quote(symbol: str, text: str) -> MarketQuote | None:
    if '="' not in text:
        return None
    payload = text.split('="', 1)[1].rsplit('"', 1)[0]
    if not payload:
        return None
    fields = payload.split(',')
    if len(fields) < 4:
        return None
    name = fields[0]
    previous_close = _to_float(fields[2])
    price = _to_float(fields[3])
    if price is None:
        return None
    return MarketQuote(code=symbol, name=name, price=price, previous_close=previous_close)


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
