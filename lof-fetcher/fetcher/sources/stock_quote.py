from __future__ import annotations

import time
from typing import Any

import httpx

TENCENT_BATCH_URL = "https://qt.gtimg.cn/q="
BATCH_SIZE = 50


def tencent_symbol(stock_code: str) -> str:
    """Map a suffixed stock code (600519.SH) to a Tencent symbol (sh600519)."""
    bare = stock_code.split(".")[0]
    suffix = stock_code.split(".")[-1].upper() if "." in stock_code else ""
    if suffix == "SH":
        return f"sh{bare}"
    if suffix == "SZ":
        return f"sz{bare}"
    if suffix in {"HK"}:
        return f"hk{bare}"
    # Fallback by leading digit
    return f"sh{bare}" if bare[:1] in {"6", "9"} else f"sz{bare}"


def _parse_line(line: str) -> dict[str, Any] | None:
    if '="' not in line:
        return None
    payload = line.split('="', 1)[1].rsplit('"', 1)[0]
    fields = payload.split("~")
    if len(fields) < 33 or not fields[2]:
        return None
    try:
        change_pct = float(fields[32]) / 100
    except (TypeError, ValueError, IndexError):
        change_pct = None
    return {"code": fields[2], "name": fields[1], "price_change_pct": change_pct}


class StockQuoteClient:
    """Batch real-time A-share quotes (Tencent) for holdings price_change_pct."""

    def __init__(self, timeout: float = 6.0) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
            trust_env=False,
        )

    def close(self) -> None:
        self._client.close()

    def fetch_change_pct(self, stock_codes: list[str]) -> dict[str, float | None]:
        """Return {suffixed_stock_code: price_change_pct or None}. Batched, low-frequency."""
        result: dict[str, float | None] = {code: None for code in stock_codes}
        symbol_to_code: dict[str, str] = {}
        for code in stock_codes:
            symbol_to_code[tencent_symbol(code)] = code
        symbols = list(symbol_to_code.keys())
        for start in range(0, len(symbols), BATCH_SIZE):
            batch = symbols[start : start + BATCH_SIZE]
            try:
                response = self._client.get(TENCENT_BATCH_URL + ",".join(batch))
                response.raise_for_status()
            except httpx.HTTPError:
                continue
            for line in response.text.strip().splitlines():
                parsed = _parse_line(line)
                if not parsed:
                    continue
                # Tencent echoes the bare numeric code in fields[2]; match by symbol prefix
                for symbol, original in symbol_to_code.items():
                    if symbol.endswith(parsed["code"]):
                        result[original] = parsed["price_change_pct"]
                        break
        return result
