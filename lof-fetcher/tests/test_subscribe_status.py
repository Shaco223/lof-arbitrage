"""PRD 1.3 AC-P6 / AC-P7: subscribe/redeem status enums + subscribe-limit parsing.

Pure unit tests (no network): exercise the mapping + limit-parse logic against the
real vendor wording captured during the 2026-06-24 intraday probe.
"""
from __future__ import annotations

from fetcher.sources.subscribe_status import (
    map_redeem_status,
    map_subscribe_status,
    parse_subscribe_limit,
)

SUBSCRIBE_ENUM = {"open", "limited", "suspended", "closed", "unknown"}
REDEEM_ENUM = {"open", "suspended", "closed", "unknown"}


def test_subscribe_status_enum_mapping():
    assert map_subscribe_status("开放申购") == "open"
    assert map_subscribe_status("限大额") == "limited"
    assert map_subscribe_status("暂停申购") == "suspended"
    assert map_subscribe_status("停止申购") == "closed"
    assert map_subscribe_status("封闭期") == "closed"
    assert map_subscribe_status(None) == "unknown"
    assert map_subscribe_status("--") == "unknown"
    assert map_subscribe_status("某种未知文案") == "unknown"


def test_redeem_status_enum_has_no_limited():
    assert map_redeem_status("开放赎回") == "open"
    assert map_redeem_status("暂停赎回") == "suspended"
    assert map_redeem_status("停止赎回") == "closed"
    assert map_redeem_status(None) == "unknown"
    # 'limited' is not a valid redeem enum value.
    assert "limited" not in REDEEM_ENUM
    assert map_redeem_status("限大额") == "unknown"


def test_limit_only_parsed_when_limited_with_number():
    # 161725: limited + "单日累计购买上限 50万元" -> 500000 / day
    res = parse_subscribe_limit(
        "limited", "限大额(单日累计购买上限 50万元。)", [], "500000"
    )
    assert res["amount"] == 500000.0
    assert res["period"] == "day"


def test_limit_yuan_unit_wording():
    # 161005: "...上限 20000元" -> 20000 / day
    res = parse_subscribe_limit(
        "limited", "限大额(单日累计购买上限 20000元。)", [], "20000"
    )
    assert res["amount"] == 20000.0
    assert res["period"] == "day"


def test_open_sentinel_maxsg_is_null():
    # 160706: open subscription, MAXSG = 1000亿 sentinel -> amount null.
    res = parse_subscribe_limit("open", None, [], "100000000000")
    assert res["amount"] is None
    assert res["period"] is None


def test_limited_without_number_is_null_amount():
    # 501203: limited but no wording number and MAXSG '--' -> amount null, status stays limited.
    res = parse_subscribe_limit("limited", None, [], "--")
    assert res["amount"] is None
    assert res["period"] is None


def test_limited_maxsg_numeric_fallback():
    # limited, no wording, but a concrete numeric MAXSG below the sentinel.
    res = parse_subscribe_limit("limited", None, [], "300000")
    assert res["amount"] == 300000.0
    assert res["period"] == "day"


def test_status_and_amount_are_independent_open_never_parses():
    # Even if a sub-sentinel MAXSG is present, a non-limited status yields no amount.
    res = parse_subscribe_limit("open", None, [], "300000")
    assert res["amount"] is None
    assert res["period"] is None



def test_normal_chinese_status_wording_for_qdii():
    on_exchange_trade = "".join(chr(x) for x in [0x573A, 0x5185, 0x4EA4, 0x6613])
    subscribe_suspended = "".join(chr(x) for x in [0x6682, 0x505C, 0x7533, 0x8D2D])
    redeem_suspended = "".join(chr(x) for x in [0x6682, 0x505C, 0x8D4E, 0x56DE])

    assert map_subscribe_status(on_exchange_trade) == "unknown"
    assert map_subscribe_status(subscribe_suspended) == "suspended"
    assert map_redeem_status(redeem_suspended) == "suspended"
