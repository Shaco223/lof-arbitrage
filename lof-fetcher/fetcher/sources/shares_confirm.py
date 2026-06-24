"""On-exchange shares + daily change + open-end confirm-day data source (PRD 1.4).

Adds four DAILY-class fields, none of which enter the minute snapshot (they live
on lof_meta, like fund_scale):

  shares_onexchange   -> jisilu "实时数据-LOF" `amount`       (场内份额, 万份)
  shares_incr_daily   -> jisilu "实时数据-LOF" `amount_incr`  (当日新增, 万份)
  purchase_confirm_day-> eastmoney jjfl 买入确认日             (T+N, 场外确认日参考)
  redeem_confirm_day  -> eastmoney jjfl 卖出确认日             (T+N, 场外确认日参考)

Cookie red line (PRD 1.4 R9): the jisilu list is member-gated (guests see only
the first 20 rows). The login Cookie is read ONLY from the JISILU_COOKIE env var
and is NEVER written to a file, committed, or logged. No Cookie / source down /
anti-scrape -> shares_onexchange & shares_incr_daily are null and the pipeline
never crashes (AC-P8).

Confirm-day semantics (PRD 1.4 R10): purchase_confirm_day / redeem_confirm_day
are the OPEN-END subscribe/redeem CONTRACT confirm day ("T+1"/"T+2"), a display
reference only -- NOT the on-exchange purchased-share sellable day. Missing ->
null (AC-P9).

NOTE: jisilu TLS fails under httpx when proxy env vars are set, so the client
uses trust_env=False (verified working 2026-06-24).
"""
from __future__ import annotations

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

# jisilu LOF realtime lists (index + stock LOF). Guests see only the first 20
# rows; full coverage needs a login Cookie via JISILU_COOKIE.
JISILU_INDEX_URL = "https://www.jisilu.cn/data/lof/index_lof_list/"
JISILU_STOCK_URL = "https://www.jisilu.cn/data/lof/stock_lof_list/"
JISILU_REFERER = "https://www.jisilu.cn/data/lof/"

F10_JJFL_URL = "https://fundf10.eastmoney.com/jjfl_{code}.html"
F10_REFERER = {"Referer": "https://fundf10.eastmoney.com/"}

_TPLUSN = re.compile(r"T\s*\+\s*(\d+)")
# Trade-rule table rows: "买入确认日</td><td>T+1</td>".
_CONFIRM_ROW = re.compile(r"([\u4e00-\u9fa5]{2,8}\u786e\u8ba4\u65e5)</td><td[^>]*>([^<]+)</td>")
_BUY_KEY = "买入确认日"
_SELL_KEY = "卖出确认日"


def _has(value: Any) -> bool:
    return value not in (None, "", "-", "--", " ")


def _to_float(value: Any) -> float | None:
    try:
        if not _has(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def get_jisilu_cookie() -> str | None:
    """Read the jisilu login Cookie from the env var only (never from a file)."""
    cookie = os.environ.get("JISILU_COOKIE")
    return cookie.strip() if cookie and cookie.strip() else None


def _normalize_tplusn(value: Any) -> str | None:
    """Normalize a raw confirm-day cell to a clean 'T+N' string, else null."""
    if not _has(value):
        return None
    m = _TPLUSN.search(str(value))
    return f"T+{m.group(1)}" if m else None


class SharesConfirmClient:
    """Fetch jisilu on-exchange shares + eastmoney jjfl confirm days.

    The jisilu shares map is fetched once for the whole batch (the list endpoint
    returns every LOF in one call); jjfl confirm days are per-code.
    """

    def __init__(self, *, timeout: float = 15.0, cookie: str | None = None) -> None:
        self._cookie = cookie if cookie is not None else get_jisilu_cookie()
        # trust_env=False avoids the proxy-induced TLS reset on jisilu.
        self._client = httpx.Client(
            timeout=timeout,
            trust_env=False,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SharesConfirmClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- jisilu on-exchange shares -------------------------------------------
    def _fetch_jisilu_one(self, url: str) -> dict[str, dict[str, Any]]:
        headers = {"Referer": JISILU_REFERER}
        if self._cookie:
            headers["Cookie"] = self._cookie
        params = {"___jsl": "LST___t", "rp": "300", "page": "1"}
        resp = self._client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        rows = (resp.json() or {}).get("rows") or []
        out: dict[str, dict[str, Any]] = {}
        for row in rows:
            cell = row.get("cell") or {}
            code = cell.get("fund_id") or row.get("id")
            if code:
                out[str(code)] = cell
        return out

    def fetch_shares_map(self) -> dict[str, dict[str, Any]]:
        """Return {code: {shares_onexchange, shares_incr_daily, source, ...}}.

        Merges index + stock LOF lists. Any source failure leaves that list out
        but never raises; codes absent from the merged map simply won't appear
        (callers treat missing as null).
        """
        merged: dict[str, Any] = {}
        for url in (JISILU_INDEX_URL, JISILU_STOCK_URL):
            try:
                merged.update(self._fetch_jisilu_one(url))
            except Exception:  # noqa: BLE001 - source down -> skip, fields null
                continue
        result: dict[str, dict[str, Any]] = {}
        for code, cell in merged.items():
            result[code] = {
                "code": code,
                "shares_onexchange": _to_float(cell.get("amount")),
                "shares_incr_daily": _to_float(cell.get("amount_incr")),
                "shares_dt": cell.get("amount_dt"),
                "source": "jisilu_lof",
            }
        return result

    # -- eastmoney jjfl confirm days -----------------------------------------
    def fetch_confirm_days(self, code: str) -> dict[str, Any]:
        """Return {purchase_confirm_day, redeem_confirm_day} as 'T+N' or null."""
        try:
            resp = self._client.get(F10_JJFL_URL.format(code=code), headers=F10_REFERER)
            resp.encoding = "utf-8"
            text = resp.text if resp.status_code == 200 else ""
            pairs = dict(_CONFIRM_ROW.findall(text))
            return {
                "code": code,
                "purchase_confirm_day": _normalize_tplusn(pairs.get(_BUY_KEY)),
                "redeem_confirm_day": _normalize_tplusn(pairs.get(_SELL_KEY)),
                "source": "eastmoney_jjfl",
            }
        except Exception:  # noqa: BLE001 - source down -> null, never crash
            return {
                "code": code,
                "purchase_confirm_day": None,
                "redeem_confirm_day": None,
                "source": "none",
            }


def fetch_shares_confirm_map(
    codes: list[str],
    *,
    client: SharesConfirmClient | None = None,
    max_workers: int = 6,
) -> dict[str, dict[str, Any]]:
    """Fetch all four PRD 1.4 daily fields for many codes.

    shares are looked up once (single list call); confirm days are per-code.
    One failure never aborts the batch; missing shares -> null. Returns
    {code: {shares_onexchange, shares_incr_daily, purchase_confirm_day,
    redeem_confirm_day, shares_source, confirm_source}}.
    """
    own_client = client is None
    client = client or SharesConfirmClient()
    results: dict[str, dict[str, Any]] = {}
    try:
        shares_map = client.fetch_shares_map()

        def _confirm(code: str) -> dict[str, Any]:
            try:
                return client.fetch_confirm_days(code)
            except Exception:  # noqa: BLE001 - defensive
                return {"code": code, "purchase_confirm_day": None,
                        "redeem_confirm_day": None, "source": "none"}

        if max_workers and max_workers > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                confirms = {c["code"]: c for c in pool.map(_confirm, codes)}
        else:
            confirms = {code: _confirm(code) for code in codes}

        for code in codes:
            sh = shares_map.get(code) or {}
            cf = confirms.get(code) or {}
            results[code] = {
                "code": code,
                "shares_onexchange": sh.get("shares_onexchange"),
                "shares_incr_daily": sh.get("shares_incr_daily"),
                "purchase_confirm_day": cf.get("purchase_confirm_day"),
                "redeem_confirm_day": cf.get("redeem_confirm_day"),
                "shares_source": sh.get("source", "none"),
                "shares_dt": sh.get("shares_dt"),
                "confirm_source": cf.get("source", "none"),
            }
    finally:
        if own_client:
            client.close()
    return results
