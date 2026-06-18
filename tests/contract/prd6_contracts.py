"""PRD §6 static API contract definitions.

These contracts do not call a live backend. They encode the field structure
stated in PRD §6 so dev-003/dev-004 can align implementation before integration
endpoints are available.
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


COMMON_RESPONSE = {
    "code": FieldSpec("integer"),
    "message": FieldSpec("string"),
    "data": FieldSpec("object"),
}

COMMON_ERROR_CODES = {0, 4001, 4010, 4040, 4290, 5000}
SOURCE_QUALITY = {"ok", "degraded", "stale"}
LOF_TYPES = {"index", "industry", "active"}

API_LOF_LIST_ITEM = {
    "code": FieldSpec("string"),
    "name": FieldSpec("string"),
    "type": FieldSpec("string", enum=tuple(sorted(LOF_TYPES))),
    "price": FieldSpec("number"),
    "iopv": FieldSpec("number"),
    "premium": FieldSpec("number"),
    "coverage": FieldSpec("number"),
    "pctile_30d": FieldSpec("number"),
    "source_quality": FieldSpec("string", enum=tuple(sorted(SOURCE_QUALITY))),
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
    "weight": FieldSpec("number"),
}
REALTIME_BLOCK = {
    "ts": FieldSpec("string"),
    "price": FieldSpec("number"),
    "iopv": FieldSpec("number"),
    "premium": FieldSpec("number"),
    "coverage": FieldSpec("number"),
    "source_quality": FieldSpec("string", enum=tuple(sorted(SOURCE_QUALITY))),
}
API_LOF_DETAIL_DATA = {
    "code": FieldSpec("string"),
    "name": FieldSpec("string"),
    "type": FieldSpec("string", enum=tuple(sorted(LOF_TYPES))),
    "scale_yi": FieldSpec("number"),
    "coverage_top10": FieldSpec("number"),
    "coverage_breakdown": FieldSpec("object"),
    "benchmark_raw": FieldSpec("string"),
    "benchmark_components": FieldSpec("array"),
    "holdings_top10": FieldSpec("array"),
    "realtime": FieldSpec("object"),
    "pctile_30d": FieldSpec("number"),
}
API_LOF_DETAIL_REQUIRED_BLOCKS = {
    "coverage_top10",
    "coverage_breakdown",
    "benchmark_components",
    "holdings_top10",
    "realtime",
    "pctile_30d",
}

HISTORY_ITEM = {
    "date": FieldSpec("string"),
    "close_price": FieldSpec("number"),
    "official_nav": FieldSpec("number"),
    "premium_close": FieldSpec("number"),
    "premium_pctile_30d": FieldSpec("number"),
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
                "price": 0.823,
                "iopv": 0.805,
                "premium": 0.0224,
                "coverage": 1.00,
                "pctile_30d": 0.82,
                "source_quality": "ok",
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
        "scale_yi": 300,
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
            {"stock_code": "600519.SH", "stock_name": "贵州茅台", "weight": 0.15}
        ],
        "realtime": {
            "ts": "2026-06-18T10:31:00+08:00",
            "price": 0.823,
            "iopv": 0.805,
            "premium": 0.0224,
            "coverage": 1.00,
            "source_quality": "ok",
        },
        "pctile_30d": 0.82,
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
