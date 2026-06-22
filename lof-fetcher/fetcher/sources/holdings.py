from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

EASTMONEY_JJCC_URL = "https://fundf10.eastmoney.com/FundArchivesDatas.aspx"
EXCHANGE_SUFFIX_SH = {"6", "9"}


@dataclass(frozen=True)
class HoldingRow:
    stock_code: str
    stock_name: str
    weight: float
    report_date: str


@dataclass
class HoldingsResult:
    code: str
    report_date: str | None
    rows: list[HoldingRow] = field(default_factory=list)
    source: str = "eastmoney_f10_jjcc"
    elapsed_ms: int = 0
    error: str = ""


_TR_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
_CODE_RE = re.compile(r">(\d{6})</a>")
_NAME_RE = re.compile(r"class='tol'><a[^>]*>([^<]+)</a>")
_PCT_RE = re.compile(r"<td class='tor'>([\d.]+)%</td>")
_REPORT_RE = re.compile(r"<font[^>]*>([\d]{4}-[\d]{2}-[\d]{2})</font>")


def stock_suffix(stock_code: str) -> str:
    """Append exchange suffix per PRD ($5.2: stock_code with exchange suffix)."""
    if stock_code[:1] in EXCHANGE_SUFFIX_SH:
        return f"{stock_code}.SH"
    return f"{stock_code}.SZ"


def parse_jjcc_html(text: str) -> tuple[str | None, list[HoldingRow]]:
    report_match = _REPORT_RE.search(text)
    report_date = report_match.group(1) if report_match else None
    rows: list[HoldingRow] = []
    for tr in _TR_RE.findall(text):
        code_match = _CODE_RE.search(tr)
        name_match = _NAME_RE.search(tr)
        pct_matches = _PCT_RE.findall(tr)
        if not (code_match and name_match and pct_matches):
            continue
        raw_code = code_match.group(1)
        try:
            weight = round(float(pct_matches[0]) / 100, 6)
        except (TypeError, ValueError):
            continue
        rows.append(
            HoldingRow(
                stock_code=stock_suffix(raw_code),
                stock_name=name_match.group(1).strip(),
                weight=weight,
                report_date=report_date or "",
            )
        )
    return report_date, rows


class HoldingsClient:
    """Fetch latest quarterly top-10 holdings from Eastmoney fund F10 (free HTML)."""

    def __init__(self, timeout: float = 8.0, retries: int = 2) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://fundf10.eastmoney.com/",
            },
            follow_redirects=True,
            trust_env=False,
        )
        self._retries = max(0, retries)

    def close(self) -> None:
        self._client.close()

    def fetch_holdings(self, code: str, topline: int = 10) -> HoldingsResult:
        result = HoldingsResult(code=code, report_date=None)
        start = time.perf_counter()
        last_error = ""
        for attempt in range(self._retries + 1):
            try:
                response = self._client.get(
                    EASTMONEY_JJCC_URL,
                    params={"type": "jjcc", "code": code, "topline": topline, "year": "", "month": ""},
                )
                response.raise_for_status()
                report_date, rows = parse_jjcc_html(response.text)
                result.report_date = report_date
                result.rows = rows[:topline]
                result.elapsed_ms = int(round((time.perf_counter() - start) * 1000))
                if not rows:
                    result.error = "empty_holdings"
                return result
            except (httpx.HTTPError, ValueError) as exc:
                last_error = f"{type(exc).__name__}"
                if attempt < self._retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
        result.elapsed_ms = int(round((time.perf_counter() - start) * 1000))
        result.error = last_error or "fetch_failed"
        return result
