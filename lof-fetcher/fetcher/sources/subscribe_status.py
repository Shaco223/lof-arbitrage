"""Subscribe/redeem status + subscribe-limit data source (PRD 1.3 production).

Promotes subscribe_status / redeem_status from placeholder "unknown" to real
values and adds subscribe_limit_amount / subscribe_limit_period, sourced from the
free Tiantian (eastmoney) mobile API fundmob_basic (SGZT / SHZT / MAXSG /
SGZTMARK / TRADEMARKLIST), with the fund overview HTML (fundf10 jbgk) as backup
and "unknown" / null as the final fallback.

These are DAILY-class fields (status/limit change at most a few times a year), so
callers refresh them into lof_meta on a daily cadence, never into the minute
snapshot (mirrors fund_scale handling).

PRD 1.3 enums:
  subscribe_status: open / limited / suspended / closed / unknown
  redeem_status:    open / suspended / closed / unknown   (no 'limited')

AC-P7 limit rule: subscribe_limit_amount is parsed ONLY when status == 'limited'
and the wording carries a concrete number; the open-subscription sentinel
MAXSG == 1000亿 (1e11) is NOT a real cap (-> null); 'limited' with no number
keeps status='limited' but amount/period=null (status and amount are independent).
"""
from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

FUNDMOB_QS = "plat=Android&appType=ttjj&product=EFund&Version=1&deviceid=1"
FUNDMOB_URL = (
    "https://fundmobapi.eastmoney.com/FundMNewApi/FundMNBasicInformation"
    "?FCODE={code}&" + FUNDMOB_QS
)
F10_HTML_URL = "https://fundf10.eastmoney.com/jbgk_{code}.html"

# Open-subscription sentinel: a MAXSG at/above this magnitude means "no real cap"
# (eastmoney returns 100000000000 == 1000亿 for open funds). Must map to null.
LIMIT_NO_CAP = 1_000_000_000.0

_UNIT_YI = "亿"   # 1e8
_UNIT_WAN = "万"  # 1e4
_LIMIT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*(亿|万)?元")
_PERIOD_DAY_HINT = "日"  # day (single-day cumulative cap wording)


def _has(value: Any) -> bool:
    return value not in (None, "", "-", "--", " ")


def _to_yuan(num: float, unit: str | None) -> float:
    if unit == _UNIT_YI:
        return num * 1e8
    if unit == _UNIT_WAN:
        return num * 1e4
    return num


# Raw vendor wording -> clean enum. Subscribe side carries 'limited'; redeem does not.
SUBSCRIBE_ENUM_MAP = {
    "开放申购": "open",      # open subscription
    "场内买入": "open",      # on-exchange buy only -> treat as open
    "限大额": "limited",          # large-amount limited
    "暂停申购": "suspended",  # suspended subscription
    "停止申购": "closed",     # stopped subscription
    "封闭期": "closed",           # closed period
    "封闭": "closed",
}
REDEEM_ENUM_MAP = {
    "开放赎回": "open",       # open redemption
    "暂停赎回": "suspended",  # suspended redemption
    "停止赎回": "closed",     # stopped redemption
    "封闭期": "closed",
    "封闭": "closed",
}


def map_subscribe_status(raw: Any) -> str:
    """Map raw vendor subscribe wording to the PRD 1.3 enum (default unknown)."""
    if not _has(raw):
        return "unknown"
    text = str(raw)
    for key, val in SUBSCRIBE_ENUM_MAP.items():
        if key in text:
            return val
    return "unknown"


def map_redeem_status(raw: Any) -> str:
    """Map raw vendor redeem wording to the PRD 1.3 enum (default unknown)."""
    if not _has(raw):
        return "unknown"
    text = str(raw)
    for key, val in REDEEM_ENUM_MAP.items():
        if key in text:
            return val
    return "unknown"


def parse_subscribe_limit(
    status: str,
    mark: Any,
    trademark_list: Any,
    max_sg: Any,
) -> dict[str, Any]:
    """Resolve subscribe_limit_amount (yuan) + subscribe_limit_period per AC-P7.

    Only status == 'limited' yields a non-null amount. Wording (SGZTMARK /
    TRADEMARKLIST) is preferred because it carries an explicit number + period;
    the numeric MAXSG is a cross-check fallback. The open sentinel MAXSG>=1e9 is
    treated as "no cap" -> null. 'limited' with no parseable number -> null amount
    (status stays 'limited'; status and amount are independent dimensions).
    """
    if status != "limited":
        return {"amount": None, "period": None, "raw": None}

    texts: list[str] = []
    if _has(mark):
        texts.append(str(mark))
    if isinstance(trademark_list, list):
        texts.extend(str(x) for x in trademark_list if _has(x))

    for text in texts:
        m = _LIMIT_RE.search(text)
        if m:
            amount = _to_yuan(float(m.group(1)), m.group(2))
            period = "day" if _PERIOD_DAY_HINT in text else None
            return {"amount": amount, "period": period, "raw": text}

    # Numeric MAXSG cross-check when wording has no number.
    try:
        max_sg_num = float(max_sg) if _has(max_sg) else None
    except (TypeError, ValueError):
        max_sg_num = None
    if max_sg_num is not None and 0 < max_sg_num < LIMIT_NO_CAP:
        return {"amount": max_sg_num, "period": "day", "raw": str(max_sg)}

    return {"amount": None, "period": None, "raw": texts[0] if texts else None}


def _unknown(code: str, reason: str) -> dict[str, Any]:
    return {
        "code": code,
        "subscribe_status": "unknown",
        "redeem_status": "unknown",
        "subscribe_limit_amount": None,
        "subscribe_limit_period": None,
        "source": "none",
        "reason": reason,
    }


class SubscribeStatusClient:
    """Fetch subscribe/redeem status + subscribe-limit for a LOF code.

    Primary: fundmob_basic (structured SGZT/SHZT/MAXSG/marks).
    Backup:  fundf10 jbgk overview HTML (trade-status span).
    Fallback: unknown / null (never raises to the caller's loop).
    """

    def __init__(self, timeout: float = 8.0) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
            trust_env=False,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SubscribeStatusClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def fetch(self, code: str) -> dict[str, Any]:
        primary = self._fetch_fundmob(code)
        if primary is not None:
            return primary
        backup = self._fetch_f10_html(code)
        if backup is not None:
            return backup
        return _unknown(code, "all_sources_failed")

    def _fetch_fundmob(self, code: str) -> dict[str, Any] | None:
        try:
            resp = self._client.get(FUNDMOB_URL.format(code=code))
            resp.raise_for_status()
            data = (resp.json() or {}).get("Datas") or {}
            if isinstance(data, list):
                data = data[0] if data else {}
            sgzt = data.get("SGZT")
            shzt = data.get("SHZT")
            if not _has(sgzt) and not _has(shzt):
                return None
            subscribe_status = map_subscribe_status(sgzt)
            redeem_status = map_redeem_status(shzt)
            limit = parse_subscribe_limit(
                subscribe_status, data.get("SGZTMARK"),
                data.get("TRADEMARKLIST"), data.get("MAXSG"),
            )
            return {
                "code": code,
                "subscribe_status": subscribe_status,
                "redeem_status": redeem_status,
                "subscribe_limit_amount": limit["amount"],
                "subscribe_limit_period": limit["period"],
                "source": "fundmob_basic",
                "subscribe_status_raw": sgzt,
                "redeem_status_raw": shzt,
                "subscribe_limit_raw": limit["raw"],
            }
        except Exception as exc:  # noqa: BLE001 - source failure -> backup
            return None

    def _fetch_f10_html(self, code: str) -> dict[str, Any] | None:
        try:
            resp = self._client.get(F10_HTML_URL.format(code=code))
            resp.encoding = "utf-8"
            if resp.status_code != 200:
                return None
            text = resp.text
            # Overview table: "申购状态：<td>VALUE</td>" /
            # "赎回状态：<td>VALUE</td>".
            sub_raw = _extract_label_value(text, "申购状态")
            red_raw = _extract_label_value(text, "赎回状态")
            if not _has(sub_raw) and not _has(red_raw):
                return None
            subscribe_status = map_subscribe_status(sub_raw)
            redeem_status = map_redeem_status(red_raw)
            # Backup HTML carries no reliable structured cap number -> null.
            return {
                "code": code,
                "subscribe_status": subscribe_status,
                "redeem_status": redeem_status,
                "subscribe_limit_amount": None,
                "subscribe_limit_period": None,
                "source": "f10_html",
                "subscribe_status_raw": sub_raw,
                "redeem_status_raw": red_raw,
                "subscribe_limit_raw": None,
            }
        except Exception:  # noqa: BLE001 - source failure -> fallback unknown
            return None


def _extract_label_value(html: str, label: str) -> str | None:
    # Match "<label>：</...><td...>VALUE</td>" tolerating tags/whitespace between.
    pattern = re.compile(
        re.escape(label) + r"[：:]\s*</[^>]+>\s*<td[^>]*>([^<]+)</td>"
    )
    m = pattern.search(html)
    if m:
        return m.group(1).strip()
    # Looser fallback: label followed by the next tag's text.
    loose = re.compile(re.escape(label) + r"[：:]\s*(?:<[^>]+>\s*)*([一-龥]{2,8})")
    m2 = loose.search(html)
    return m2.group(1).strip() if m2 else None


def fetch_subscribe_status_map(
    codes: list[str],
    *,
    client: SubscribeStatusClient | None = None,
    max_workers: int = 6,
    pause_seconds: float = 0.0,
) -> dict[str, dict[str, Any]]:
    """Fetch status+limit for many codes; one failure never aborts the batch.

    Returns {code: {subscribe_status, redeem_status, subscribe_limit_amount,
    subscribe_limit_period, source, ...}}. Daily-class call (low frequency).
    """
    own_client = client is None
    client = client or SubscribeStatusClient()
    results: dict[str, dict[str, Any]] = {}
    try:
        def _one(code: str) -> dict[str, Any]:
            try:
                return client.fetch(code)
            except Exception as exc:  # noqa: BLE001 - defensive; fetch already guards
                return _unknown(code, f"error:{type(exc).__name__}")

        if max_workers and max_workers > 1 and not pause_seconds:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                for res in pool.map(_one, codes):
                    results[res["code"]] = res
        else:
            for code in codes:
                results[code] = _one(code)
                if pause_seconds:
                    time.sleep(pause_seconds)
    finally:
        if own_client:
            client.close()
    return results
