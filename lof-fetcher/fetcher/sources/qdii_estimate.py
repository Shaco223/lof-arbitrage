from __future__ import annotations

from dataclasses import dataclass
import re
import time
from typing import Any

import httpx


@dataclass(frozen=True)
class QdiiReferenceMapping:
    code: str
    reference_index_code: str
    reference_index_name: str
    asset_region: str
    currency: str
    formula_type: str = "reference_index_estimate"


QDII_REFERENCE_MAPPINGS: dict[str, QdiiReferenceMapping] = {
    "510900": QdiiReferenceMapping("510900", "hkHSCEI", "????????", "hong_kong", "HKD"),
    "159920": QdiiReferenceMapping("159920", "hkHSI", "????", "hong_kong", "HKD"),
    "159941": QdiiReferenceMapping("159941", "usIXIC", "????????", "us", "USD"),
    "513500": QdiiReferenceMapping("513500", "usINX", "??500??", "us", "USD"),
    "161125": QdiiReferenceMapping("161125", "usINX", "??500??", "us", "USD"),
}
QDII_HIGH_CODES = set(QDII_REFERENCE_MAPPINGS)
QDII_FX_SYMBOLS = {
    "HKD": "fx_shkdcny",
    "USD": "fx_susdcny",
}
QDII_FIELD_NAMES = (
    "qdii_estimate_nav",
    "qdii_estimate_premium",
    "qdii_reference_index_code",
    "qdii_reference_index_name",
    "qdii_reference_index_change_pct",
    "qdii_fx_change_pct",
    "qdii_estimate_quality",
    "qdii_estimate_source",
    "qdii_nav_date",
)


def qdii_null_fields() -> dict[str, Any]:
    return {
        "qdii_estimate_nav": None,
        "qdii_estimate_premium": None,
        "qdii_reference_index_code": None,
        "qdii_reference_index_name": None,
        "qdii_reference_index_change_pct": None,
        "qdii_fx_change_pct": None,
        "qdii_estimate_quality": "unavailable",
        "qdii_estimate_source": None,
        "qdii_nav_date": None,
    }


def calculate_qdii_estimate(
    code: str,
    price: float | None,
    nav_official: float | None,
    nav_official_date: str | None,
    reference_index_change_pct: float | None,
    fx_change_pct: float | None,
) -> dict[str, Any]:
    mapping = QDII_REFERENCE_MAPPINGS.get(str(code).zfill(6))
    if not mapping:
        return qdii_null_fields()
    if (
        price is None
        or nav_official is None
        or nav_official <= 0
        or reference_index_change_pct is None
        or fx_change_pct is None
    ):
        result = qdii_null_fields()
        result.update(
            {
                "qdii_reference_index_code": mapping.reference_index_code,
                "qdii_reference_index_name": mapping.reference_index_name,
                "qdii_reference_index_change_pct": reference_index_change_pct,
                "qdii_fx_change_pct": fx_change_pct,
                "qdii_nav_date": nav_official_date,
            }
        )
        return result

    estimate_nav = round(nav_official * (1 + reference_index_change_pct) * (1 + fx_change_pct), 6)
    estimate_premium = round(price / estimate_nav - 1, 6) if estimate_nav > 0 else None
    return {
        "qdii_estimate_nav": estimate_nav if estimate_premium is not None else None,
        "qdii_estimate_premium": estimate_premium,
        "qdii_reference_index_code": mapping.reference_index_code,
        "qdii_reference_index_name": mapping.reference_index_name,
        "qdii_reference_index_change_pct": round(reference_index_change_pct, 6),
        "qdii_fx_change_pct": round(fx_change_pct, 6),
        "qdii_estimate_quality": "high",
        "qdii_estimate_source": "reference_index_estimate",
        "qdii_nav_date": nav_official_date,
    }


def build_qdii_fields_from_payload(
    code: str,
    price: float | None,
    nav_official: float | None,
    nav_official_date: str | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    qdii_payload = payload.get("qdii") or {}
    return calculate_qdii_estimate(
        code=code,
        price=price,
        nav_official=nav_official,
        nav_official_date=nav_official_date,
        reference_index_change_pct=_number_or_none(qdii_payload.get("reference_index_change_pct")),
        fx_change_pct=_number_or_none(qdii_payload.get("fx_change_pct")),
    )


def fetch_qdii_reference_payloads(codes: list[str], timeout: float = 5.0) -> dict[str, dict[str, Any]]:
    wanted = [str(code).zfill(6) for code in codes if str(code).zfill(6) in QDII_REFERENCE_MAPPINGS]
    if not wanted:
        return {}

    client = httpx.Client(
        timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"},
        follow_redirects=True,
        trust_env=False,
    )
    try:
        index_changes = _fetch_reference_index_changes(client, wanted)
        fx_changes = _fetch_fx_changes(client, wanted)
    finally:
        client.close()

    payloads: dict[str, dict[str, Any]] = {}
    for code in wanted:
        mapping = QDII_REFERENCE_MAPPINGS[code]
        payloads[code] = {
            "reference_index_code": mapping.reference_index_code,
            "reference_index_name": mapping.reference_index_name,
            "reference_index_change_pct": index_changes.get(mapping.reference_index_code),
            "fx_symbol": QDII_FX_SYMBOLS.get(mapping.currency),
            "fx_change_pct": fx_changes.get(mapping.currency),
            "source": "tencent_reference_index+sina_fx",
        }
    return payloads


def parse_tencent_reference_index_payload(text: str) -> dict[str, float]:
    result: dict[str, float] = {}
    for symbol, payload in re.findall(r'v_([A-Za-z0-9]+)="([^"]*)";?', text):
        fields = payload.split("~")
        if len(fields) < 5:
            continue
        current = _number_or_none(fields[3])
        previous_close = _number_or_none(fields[4])
        if current is None or previous_close is None or previous_close <= 0:
            continue
        result[symbol] = round(current / previous_close - 1, 6)
    return result


def parse_sina_fx_payload(text: str) -> dict[str, float]:
    result: dict[str, float] = {}
    for symbol, payload in re.findall(r'hq_str_(fx_s[a-z0-9]+cny)="([^"]*)";?', text):
        fields = payload.split(",")
        pct_value = _number_or_none(fields[10]) if len(fields) > 10 else None
        if pct_value is None:
            continue
        result[symbol] = round(pct_value / 100, 6)
    return result


def _number_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fetch_reference_index_changes(client: httpx.Client, codes: list[str]) -> dict[str, float]:
    symbols = sorted({QDII_REFERENCE_MAPPINGS[code].reference_index_code for code in codes})
    if not symbols:
        return {}
    try:
        response = client.get(f"https://qt.gtimg.cn/q={','.join(symbols)}")
        response.raise_for_status()
        return parse_tencent_reference_index_payload(response.text)
    except (httpx.HTTPError, ValueError):
        return {}


def _fetch_fx_changes(client: httpx.Client, codes: list[str]) -> dict[str, float]:
    symbols_by_currency = {
        QDII_REFERENCE_MAPPINGS[code].currency: QDII_FX_SYMBOLS[QDII_REFERENCE_MAPPINGS[code].currency]
        for code in codes
        if QDII_REFERENCE_MAPPINGS[code].currency in QDII_FX_SYMBOLS
    }
    if not symbols_by_currency:
        return {}
    try:
        rn = int(time.time() * 1000)
        response = client.get(f"https://hq.sinajs.cn/rn={rn}&list={','.join(sorted(symbols_by_currency.values()))}")
        response.raise_for_status()
        by_symbol = parse_sina_fx_payload(response.text)
    except (httpx.HTTPError, ValueError):
        return {}
    return {
        currency: by_symbol[symbol]
        for currency, symbol in symbols_by_currency.items()
        if symbol in by_symbol
    }
