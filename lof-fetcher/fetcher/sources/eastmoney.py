from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class FundMetadata:
    code: str
    name: str | None
    exists: bool
    raw_name: str | None = None
    note: str = ""


class EastmoneyFundMetadataClient:
    def __init__(self, timeout: float = 10.0) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
            trust_env=False,
        )

    def close(self) -> None:
        self._client.close()

    def fetch_metadata(self, code: str) -> FundMetadata:
        url = f"https://fund.eastmoney.com/pingzhongdata/{code}.js"
        try:
            response = self._client.get(url)
            if response.status_code != 200:
                return FundMetadata(code=code, name=None, exists=False, note=f"http_status={response.status_code}")
            text = response.text
            name = _extract_js_string(text, "fS_name")
            raw_code = _extract_js_string(text, "fS_code")
            if raw_code and raw_code != code:
                return FundMetadata(code=code, name=name, exists=False, raw_name=name, note=f"code_mismatch={raw_code}")
            if not name:
                return FundMetadata(code=code, name=None, exists=False, note="missing_fund_name")
            return FundMetadata(code=code, name=name, exists=True, raw_name=name, note="ok")
        except httpx.HTTPError as exc:
            return FundMetadata(code=code, name=None, exists=False, note=f"network_error={type(exc).__name__}")


def validate_watchlist_rows(rows: list[Any], client: EastmoneyFundMetadataClient) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for row in rows:
        meta = client.fetch_metadata(row.code)
        risk = "ok"
        reason = meta.note
        if not meta.exists:
            risk = "suspect"
        elif row.status == "pending_verify":
            risk = "pending_verify"
            reason = "PRD 标记为 pending_verify；需人工确认是否已转型/合并/清盘"
        elif meta.name and _normalize_name(meta.name) != _normalize_name(row.name):
            risk = "name_changed"
            reason = f"official_name={meta.name}"
        results.append(
            {
                "code": row.code,
                "watchlist_name": row.name,
                "official_name": meta.name or "",
                "type": row.type,
                "scale_yi": str(row.scale_yi),
                "status": row.status,
                "risk": risk,
                "reason": reason,
            }
        )
    return results


def _extract_js_string(text: str, var_name: str) -> str | None:
    match = re.search(rf'var\s+{re.escape(var_name)}\s*=\s*"([^"]*)"', text)
    if match:
        return match.group(1).strip()
    return None


def _normalize_name(name: str) -> str:
    return (
        name.replace("（", "(")
        .replace("）", ")")
        .replace(" ", "")
        .replace("指数", "")
        .replace("混合", "")
        .lower()
    )
