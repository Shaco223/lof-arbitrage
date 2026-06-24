"""PRD §6 static API contract definitions (PRD 1.2 alignment).

These contracts encode the field structure declared in PRD §6 (1.2).
They run without a live backend and are reused by tests/contract and
tests/e2e/test_real_api_acceptance.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

JsonType = Literal["string", "number", "integer", "array", "object"]


@dataclass(frozen=True)
class FieldSpec:
    type: JsonType
    required: bool = True
    enum: tuple[Any, ...] | None = None
    nullable: bool = False


COMMON_RESPONSE = {
    "code": FieldSpec("integer"),
    "message": FieldSpec("string"),
    "data": FieldSpec("object"),
}

COMMON_ERROR_CODES = {0, 4001, 4010, 4040, 4290, 5000}
SOURCE_QUALITY = {"ok", "degraded", "stale"}
LOF_TYPES = {"index", "industry", "active"}
LOF_STATUS = {"active", "active_low_liquidity"}
SUBSCRIBE_STATUS = {"open", "limited", "suspended", "closed", "unknown"}
REDEEM_STATUS = {"open", "suspended", "closed", "unknown"}
SUBSCRIBE_LIMIT_PERIOD = {"day"}


API_LOF_LIST_ITEM = {
    "code": FieldSpec("string"),
    "name": FieldSpec("string"),
    "type": FieldSpec("string", enum=tuple(sorted(LOF_TYPES))),
    "status": FieldSpec("string", enum=tuple(sorted(LOF_STATUS))),
    "price": FieldSpec("number", nullable=True),
    "price_change_pct": FieldSpec("number", nullable=True),
    "volume_amount": FieldSpec("number", nullable=True),
    "iopv": FieldSpec("number", nullable=True),
    "premium": FieldSpec("number", nullable=True),
    "nav_official": FieldSpec("number", nullable=True),
    "nav_official_date": FieldSpec("string", nullable=True),
    "premium_nav": FieldSpec("number", nullable=True),
    "premium_error": FieldSpec("number", nullable=True),
    "coverage": FieldSpec("number", nullable=True),
    "pctile_30d": FieldSpec("number", nullable=True),
    "source_quality": FieldSpec("string", enum=tuple(sorted(SOURCE_QUALITY))),
    "subscribe_status": FieldSpec("string", required=False, enum=tuple(sorted(SUBSCRIBE_STATUS)), nullable=True),
    "redeem_status": FieldSpec("string", required=False, enum=tuple(sorted(REDEEM_STATUS)), nullable=True),
    "fund_scale": FieldSpec("number", required=False, nullable=True),
    "circulating_shares": FieldSpec("number", required=False, nullable=True),
    "subscribe_limit_amount": FieldSpec("number", required=False, nullable=True),
    "subscribe_limit_period": FieldSpec("string", required=False, enum=tuple(sorted(SUBSCRIBE_LIMIT_PERIOD)), nullable=True),
}
API_LOF_LIST_ITEM_LEGACY_REQUIRED = {
    "code", "name", "type", "price", "iopv", "premium",
    "coverage", "pctile_30d", "source_quality",
}
API_LOF_LIST_DATA = {
    "ts": FieldSpec("string"),
    "items": FieldSpec("array"),
}

COVERAGE_BREAKDOWN = {
    "top10_weight": FieldSpec("number"),
    "benchmark_assigned_weight": FieldSpec("number"),
    "cash_weight": FieldSpec("number"),
}
BENCHMARK_COMPONENT = {
    "index_code": FieldSpec("string"),
    "name": FieldSpec("string"),
    "weight": FieldSpec("number"),
}
HOLDING_TOP10_ITEM = {
    "stock_code": FieldSpec("string"),
    "stock_name": FieldSpec("string"),
    "weight": FieldSpec("number", nullable=True),
    "price_change_pct": FieldSpec("number", required=False, nullable=True),
    "contribution_pct": FieldSpec("number", nullable=True),
}
REALTIME_BLOCK = {
    "ts": FieldSpec("string"),
    "price": FieldSpec("number", nullable=True),
    "iopv": FieldSpec("number", nullable=True),
    "premium": FieldSpec("number", nullable=True),
    "coverage": FieldSpec("number", nullable=True),
    "source_quality": FieldSpec("string", enum=tuple(sorted(SOURCE_QUALITY))),
}


API_LOF_DETAIL_DATA = {
    # PRD 1.2: list 全部字段 + 详情专属字段
    "code": FieldSpec("string"),
    "name": FieldSpec("string"),
    "type": FieldSpec("string", enum=tuple(sorted(LOF_TYPES))),
    "status": FieldSpec("string", enum=tuple(sorted(LOF_STATUS))),
    "scale_yi": FieldSpec("number", nullable=True),
    "fund_scale": FieldSpec("number", required=False, nullable=True),
    "circulating_shares": FieldSpec("number", required=False, nullable=True),
    "price": FieldSpec("number", nullable=True),
    "price_change_pct": FieldSpec("number", nullable=True),
    "volume_amount": FieldSpec("number", nullable=True),
    "iopv": FieldSpec("number", nullable=True),
    "premium": FieldSpec("number", nullable=True),
    "nav_official": FieldSpec("number", nullable=True),
    "nav_official_date": FieldSpec("string", nullable=True),
    "premium_nav": FieldSpec("number", nullable=True),
    "premium_error": FieldSpec("number", nullable=True),
    "nav_estimate_error_pct": FieldSpec("number", nullable=True),
    "coverage": FieldSpec("number", nullable=True),
    "pctile_30d": FieldSpec("number", nullable=True),
    "source_quality": FieldSpec("string", enum=tuple(sorted(SOURCE_QUALITY))),
    "subscribe_status": FieldSpec("string", required=False, enum=tuple(sorted(SUBSCRIBE_STATUS)), nullable=True),
    "redeem_status": FieldSpec("string", required=False, enum=tuple(sorted(REDEEM_STATUS)), nullable=True),
    "subscribe_limit_amount": FieldSpec("number", required=False, nullable=True),
    "subscribe_limit_period": FieldSpec("string", required=False, enum=tuple(sorted(SUBSCRIBE_LIMIT_PERIOD)), nullable=True),
    "coverage_top10": FieldSpec("number", nullable=True),
    "coverage_breakdown": FieldSpec("object"),
    "benchmark_raw": FieldSpec("string", nullable=True),
    "benchmark_components": FieldSpec("array"),
    "holdings_top10": FieldSpec("array"),
    "realtime": FieldSpec("object", nullable=True),
}
API_LOF_DETAIL_REQUIRED_BLOCKS = {
    "coverage_top10",
    "coverage_breakdown",
    "benchmark_components",
    "holdings_top10",
    "realtime",
    "pctile_30d",
}
API_LOF_DETAIL_NEW_FIELDS_PRD_1_2 = {
    "status", "price_change_pct", "volume_amount", "nav_official",
    "nav_official_date", "premium_nav", "premium_error",
    "nav_estimate_error_pct", "fund_scale", "circulating_shares",
    "subscribe_status", "redeem_status",
}


def pick(spec, keys):
    """Return a sub-spec containing only ``keys`` (used for 1.1 legacy smoke)."""
    missing = sorted(keys - set(spec))
    assert not missing, f"pick() got keys not in spec: {missing}"
    return {key: field for key, field in spec.items() if key in keys}


# PRD 1.1 legacy subset: the local Python fetcher sample-output still emits only
# 1.1 fields, so offline smoke (AC-I1/AC-I2) validates against the legacy subset.
# Full 1.2 validation is covered by the real local API e2e suite.
API_LOF_LIST_ITEM_LEGACY = pick(API_LOF_LIST_ITEM, API_LOF_LIST_ITEM_LEGACY_REQUIRED)
API_LOF_DETAIL_DATA_LEGACY_KEYS = {
    "code", "name", "type", "scale_yi", "pctile_30d",
    "coverage_top10", "coverage_breakdown", "benchmark_raw",
    "benchmark_components", "holdings_top10", "realtime",
}
API_LOF_DETAIL_DATA_LEGACY = pick(API_LOF_DETAIL_DATA, API_LOF_DETAIL_DATA_LEGACY_KEYS)

HISTORY_ITEM = {
    "date": FieldSpec("string"),
    "close_price": FieldSpec("number", nullable=True),
    # 最新交易日净值 T+1 未披露时合法为 null（AC-H4：缺 official_nav 时 premium_close=null）
    "official_nav": FieldSpec("number", nullable=True),
    "premium_close": FieldSpec("number", nullable=True),
    # AC-H5：不足 30 个有效日时分位返回 null（禁合成凑满）
    "premium_pctile_30d": FieldSpec("number", nullable=True),
    # PRD 1.2.3 选填：预估收盘溢价 / 溢价偏差，可为 null
    "premium_estimate_close": FieldSpec("number", required=False, nullable=True),
    "premium_deviation": FieldSpec("number", required=False, nullable=True),
}
API_LOF_HISTORY_DATA = {
    "code": FieldSpec("string"),
    "granularity": FieldSpec("string", enum=("day", "minute")),
    "items": FieldSpec("array"),
}

INGEST_REALTIME_HEADER = {"X-Ingest-Token": FieldSpec("string")}
INGEST_REALTIME_ITEM = {
    "code": FieldSpec("string"),
    "price": FieldSpec("number"),
    "iopv": FieldSpec("number"),
    "premium": FieldSpec("number"),
    "coverage": FieldSpec("number"),
    "source_quality": FieldSpec("string", enum=tuple(sorted(SOURCE_QUALITY))),
}
INGEST_REALTIME_BODY = {
    "ts": FieldSpec("string"),
    "items": FieldSpec("array"),
}
INGEST_REALTIME_DATA = {
    "accepted": FieldSpec("integer"),
    "rejected": FieldSpec("integer"),
}
INGEST_REALTIME_ERROR_CODES = {4001, 4010, 4290}


def assert_required_keys(name: str, payload: dict[str, Any], spec: dict[str, FieldSpec]) -> None:
    missing = sorted(key for key, field in spec.items() if field.required and key not in payload)
    assert not missing, f"{name} missing required keys: {missing}"


def assert_no_unknown_keys(name: str, payload: dict[str, Any], spec: dict[str, FieldSpec]) -> None:
    unknown = sorted(set(payload) - set(spec))
    assert not unknown, f"{name} has unknown keys: {unknown}"


def assert_field_types(name: str, payload: dict[str, Any], spec: dict[str, FieldSpec]) -> None:
    for key, field in spec.items():
        if key not in payload:
            continue
        value = payload[key]
        if value is None:
            assert field.nullable or not field.required, f"{name}.{key} should not be null"
            continue
        if field.type == "string":
            assert isinstance(value, str), f"{name}.{key} should be string"
        elif field.type == "number":
            assert isinstance(value, (int, float)) and not isinstance(value, bool), f"{name}.{key} should be number"
        elif field.type == "integer":
            assert isinstance(value, int) and not isinstance(value, bool), f"{name}.{key} should be integer"
        elif field.type == "array":
            assert isinstance(value, list), f"{name}.{key} should be array"
        elif field.type == "object":
            assert isinstance(value, dict), f"{name}.{key} should be object"

        if field.enum is not None:
            assert value in field.enum, f"{name}.{key} should be one of {field.enum}, got {value!r}"


def assert_contract(name: str, payload: dict[str, Any], spec: dict[str, FieldSpec]) -> None:
    assert_required_keys(name, payload, spec)
    assert_no_unknown_keys(name, payload, spec)
    assert_field_types(name, payload, spec)


API_LOF_LIST_SAMPLE = {
    "code": 0,
    "message": "ok",
    "data": {
        "ts": "2026-06-18T10:31:00+08:00",
        "items": [
            {
                "code": "161725",
                "name": "招商中证白酒(LOF)A",
                "type": "index",
                "status": "active",
                "price": 0.823,
                "price_change_pct": 0.0123,
                "volume_amount": 18650.42,
                "iopv": 0.805,
                "premium": 0.0224,
                "nav_official": 0.802,
                "nav_official_date": "2026-06-17",
                "premium_nav": 0.0262,
                "premium_error": 0.003,
                "coverage": 1.00,
                "pctile_30d": 0.82,
                "source_quality": "ok",
                "subscribe_status": "limited",
                "redeem_status": "open",
                "fund_scale": 300.0,
                "circulating_shares": 12.5,
                "subscribe_limit_amount": 500000.0,
                "subscribe_limit_period": "day",
            }
        ],
    },
}

API_LOF_DETAIL_SAMPLE = {
    "code": 0,
    "message": "ok",
    "data": {
        "code": "161725",
        "name": "招商中证白酒(LOF)A",
        "type": "index",
        "status": "active",
        "scale_yi": 300,
        "fund_scale": 300.0,
        "circulating_shares": 12.5,
        "price": 0.823,
        "price_change_pct": 0.0123,
        "volume_amount": 18650.42,
        "iopv": 0.805,
        "premium": 0.0224,
        "nav_official": 0.802,
        "nav_official_date": "2026-06-17",
        "premium_nav": 0.0262,
        "premium_error": 0.003,
        "nav_estimate_error_pct": 0.00374,
        "coverage": 1.00,
        "pctile_30d": 0.82,
        "source_quality": "ok",
        "subscribe_status": "limited",
        "redeem_status": "open",
        "subscribe_limit_amount": 500000.0,
        "subscribe_limit_period": "day",
        "coverage_top10": 0.93,
        "coverage_breakdown": {
            "top10_weight": 0.93,
            "benchmark_assigned_weight": 0.95,
            "cash_weight": 0.05,
        },
        "benchmark_raw": "中证白酒指数收益率×95%+银行活期存款利率(税后)×5%",
        "benchmark_components": [
            {"index_code": "399997.SZ", "name": "中证白酒指数", "weight": 0.95},
            {"index_code": "CASH", "name": "银行活期", "weight": 0.05},
        ],
        "holdings_top10": [
            {
                "stock_code": "600519.SH",
                "stock_name": "贵州茅台",
                "weight": 0.15,
                "price_change_pct": 0.0152,
                "contribution_pct": 0.00228,
            }
        ],
        "realtime": {
            "ts": "2026-06-18T10:31:00+08:00",
            "price": 0.823,
            "iopv": 0.805,
            "premium": 0.0224,
            "coverage": 1.00,
            "source_quality": "ok",
        },
    },
}

API_LOF_HISTORY_SAMPLE = {
    "code": 0,
    "message": "ok",
    "data": {
        "code": "161725",
        "granularity": "day",
        "items": [
            {
                "date": "2026-05-19",
                "close_price": 0.812,
                "official_nav": 0.798,
                "premium_close": 0.0175,
                "premium_pctile_30d": 0.71,
            }
        ],
    },
}

INGEST_REALTIME_REQUEST_SAMPLE = {
    "headers": {"X-Ingest-Token": "<UNICLOUD_INGEST_TOKEN>"},
    "body": {
        "ts": "2026-06-18T10:31:00+08:00",
        "items": [
            {
                "code": "161725",
                "price": 0.823,
                "iopv": 0.805,
                "premium": 0.0224,
                "coverage": 1.00,
                "source_quality": "ok",
            }
        ],
    },
}
INGEST_REALTIME_RESPONSE_SAMPLE = {
    "code": 0,
    "message": "ok",
    "data": {"accepted": 30, "rejected": 0},
}
