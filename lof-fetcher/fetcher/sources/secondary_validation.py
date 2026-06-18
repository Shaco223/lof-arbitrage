from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from statistics import mean
from typing import Literal

import httpx

from fetcher.sources.csv_assets import LofMeta

Recommendation = Literal["keep", "rename", "type_fix", "replace", "phase2_qdii", "manual_review"]


@dataclass(frozen=True)
class VenueQuote:
    source: str
    name: str
    price: float | None
    volume: float | None
    amount: float | None
    timestamp: str | None
    is_tradable: bool


@dataclass(frozen=True)
class FundNav:
    source: str
    name: str
    nav_date: str | None
    nav: float | None
    estimate: float | None
    estimate_time: str | None
    has_nav: bool


@dataclass(frozen=True)
class ActivityStats:
    source: str
    days: int
    avg_amount: float | None
    active_days: int
    status: str


@dataclass(frozen=True)
class SecondaryValidationResult:
    code: str
    watchlist_name: str
    venue_name: str
    nav_name: str
    ping_name: str
    trading_status: str
    fund_type_verified: str
    is_lof: bool
    is_qdii: bool
    has_nav: bool
    has_venue_quote: bool
    latest_scale_yi: float | None
    avg_amount_20d: float | None
    activity_status: str
    name_compare: str
    recommendation: Recommendation
    evidence: str


class EastmoneySecondaryValidationClient:
    def __init__(self, timeout: float = 10.0) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"},
            follow_redirects=True,
            trust_env=False,
        )

    def close(self) -> None:
        self._client.close()

    def fetch_venue_quote(self, code: str) -> VenueQuote:
        secid = _secid(code)
        url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f57,f58,f43,f47,f48,f60"
        try:
            data = self._client.get(url).json().get("data") or {}
            price = _scaled_number(data.get("f43"))
            volume = _to_float(data.get("f47"))
            amount = _to_float(data.get("f48"))
            name = str(data.get("f58") or "")
            return VenueQuote(
                source="eastmoney_quote",
                name=name,
                price=price,
                volume=volume,
                amount=amount,
                timestamp=None,
                is_tradable=bool(name and price and price > 0 and amount and amount > 0),
            )
        except (httpx.HTTPError, json.JSONDecodeError, ValueError):
            return VenueQuote("eastmoney_quote", "", None, None, None, None, False)

    def fetch_nav(self, code: str) -> FundNav:
        url = f"https://fundgz.1234567.com.cn/js/{code}.js?rt={int(time.time() * 1000)}"
        try:
            text = self._client.get(url).text
            match = re.search(r"jsonpgz\((.*)\);?", text)
            data = json.loads(match.group(1)) if match else {}
            nav = _to_float(data.get("dwjz"))
            estimate = _to_float(data.get("gsz"))
            return FundNav(
                source="fundgz_1234567",
                name=str(data.get("name") or ""),
                nav_date=data.get("jzrq"),
                nav=nav,
                estimate=estimate,
                estimate_time=data.get("gztime"),
                has_nav=bool(nav and nav > 0),
            )
        except (httpx.HTTPError, json.JSONDecodeError, AttributeError, ValueError):
            return FundNav("fundgz_1234567", "", None, None, None, None, False)

    def fetch_activity(self, code: str) -> ActivityStats:
        secid = _secid(code)
        url = (
            "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6"
            "&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&lmt=20&end=20500101"
        )
        try:
            data = self._client.get(url).json().get("data") or {}
            amounts = []
            for line in data.get("klines") or []:
                fields = line.split(",")
                if len(fields) >= 7:
                    amount = _to_float(fields[6])
                    if amount is not None:
                        amounts.append(amount)
            avg_amount = mean(amounts) if amounts else None
            active_days = sum(1 for amount in amounts if amount > 0)
            status = _activity_status(avg_amount, active_days)
            return ActivityStats("eastmoney_kline", len(amounts), avg_amount, active_days, status)
        except (httpx.HTTPError, json.JSONDecodeError, ValueError):
            return ActivityStats("eastmoney_kline", 0, None, 0, "unknown")


def classify_watchlist_row(
    row: LofMeta,
    venue: VenueQuote,
    nav: FundNav,
    activity: ActivityStats,
    ping_name: str = "",
) -> SecondaryValidationResult:
    is_lof = _is_lof(row.name, venue.name, nav.name)
    is_qdii = _is_qdii(venue.name, nav.name) or (not venue.name and _is_qdii(row.name, row.benchmark_raw))
    fund_type = _verified_type(row, is_qdii)
    name_compare = _compare_names(row.name, venue.name, nav.name, ping_name)
    latest_scale_yi = row.scale_yi
    recommendation = _recommend(row, venue, nav, activity, is_lof, is_qdii, name_compare)
    evidence = "; ".join(
        part
        for part in [
            f"venue={venue.name or '-'} price={venue.price or '-'} amount={venue.amount or '-'}",
            f"nav={nav.name or '-'} nav_date={nav.nav_date or '-'}",
            f"activity={activity.status} avg20={round(activity.avg_amount, 2) if activity.avg_amount else '-'}",
            f"name_compare={name_compare}",
        ]
    )
    return SecondaryValidationResult(
        code=row.code,
        watchlist_name=row.name,
        venue_name=venue.name,
        nav_name=nav.name,
        ping_name=ping_name,
        trading_status="tradable" if venue.is_tradable else "not_tradable_or_suspended",
        fund_type_verified=fund_type,
        is_lof=is_lof,
        is_qdii=is_qdii,
        has_nav=nav.has_nav,
        has_venue_quote=bool(venue.name),
        latest_scale_yi=latest_scale_yi,
        avg_amount_20d=activity.avg_amount,
        activity_status=activity.status,
        name_compare=name_compare,
        recommendation=recommendation,
        evidence=evidence,
    )


def _secid(code: str) -> str:
    return f"1.{code}" if code.startswith("5") else f"0.{code}"


def _scaled_number(value: object) -> float | None:
    number = _to_float(value)
    if number is None or number <= 0:
        return number
    return round(number / 1000, 6)


def _to_float(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _activity_status(avg_amount: float | None, active_days: int) -> str:
    if avg_amount is None:
        return "no_kline"
    if active_days < 10:
        return "inactive"
    if avg_amount >= 5_000_000:
        return "active"
    if avg_amount >= 500_000:
        return "low_active"
    return "inactive"


def _is_lof(*names: str) -> bool:
    joined = " ".join(name.upper() for name in names if name)
    return "LOF" in joined or "基金" in joined


def _is_qdii(*texts: str) -> bool:
    joined = " ".join(text.upper() for text in texts if text)
    keywords = ["QDII", "标普", "纳斯达克", "欧洲", "黄金", "油气", "石油", "ESTOXX", "全球", "FTSE"]
    return any(keyword.upper() in joined for keyword in keywords)


def _verified_type(row: LofMeta, is_qdii: bool) -> str:
    if is_qdii:
        return "QDII"
    if row.type == "index":
        return "指数"
    if row.type == "industry":
        return "行业指数"
    if row.type == "active":
        return "主动"
    return "其他"


def _normalize_name(name: str) -> set[str]:
    cleaned = re.sub(r"[（）()A-Za-z\s]+", "", name)
    stopwords = ["指数", "基金", "联接", "混合", "分级", "行业", "主题", "公司", "证券投资", "开放式"]
    for word in stopwords:
        cleaned = cleaned.replace(word, "")
    tokens = {token for token in re.split(r"[·\-_/]+", cleaned) if token}
    if cleaned:
        tokens.add(cleaned)
    return tokens


def _compare_names(watchlist_name: str, venue_name: str, nav_name: str, ping_name: str) -> str:
    venue_nav_consistent = bool(venue_name and nav_name and _has_overlap(venue_name, nav_name))
    watchlist_venue_match = bool(venue_name and _has_overlap(watchlist_name, venue_name))
    watchlist_nav_match = bool(nav_name and _has_overlap(watchlist_name, nav_name))
    if watchlist_venue_match and watchlist_nav_match:
        return "multi_source_match"
    if watchlist_venue_match or watchlist_nav_match:
        if venue_nav_consistent:
            return "true_rename_or_share_class_change"
        return "venue_nav_divergence"
    if venue_nav_consistent:
        return "true_rename_or_share_class_change"
    if nav_name and watchlist_nav_match:
        return "nav_match_venue_abbrev"
    if venue_name and nav_name and not _has_overlap(venue_name, nav_name):
        return "interface_mapping_suspect"
    if ping_name and not _has_overlap(watchlist_name, ping_name):
        return "ping_share_class_or_mapping_diff"
    return "manual_review"


def _has_overlap(left: str, right: str) -> bool:
    left_tokens = _normalize_name(left)
    right_tokens = _normalize_name(right)
    if not left_tokens or not right_tokens:
        return False
    return any(token in right for token in left_tokens) or any(token in left for token in right_tokens) or bool(left_tokens & right_tokens)


def _recommend(
    row: LofMeta,
    venue: VenueQuote,
    nav: FundNav,
    activity: ActivityStats,
    is_lof: bool,
    is_qdii: bool,
    name_compare: str,
) -> Recommendation:
    if not venue.is_tradable or activity.status in {"inactive", "no_kline"}:
        if is_qdii:
            return "phase2_qdii"
        return "replace"
    if is_qdii:
        return "phase2_qdii"
    if not is_lof or not nav.has_nav:
        return "manual_review"
    if row.status == "pending_verify":
        return "rename"
    if name_compare == "interface_mapping_suspect":
        return "manual_review"
    if name_compare in {"true_rename_or_share_class_change", "nav_match_venue_abbrev", "ping_share_class_or_mapping_diff"}:
        return "rename"
    return "keep"
