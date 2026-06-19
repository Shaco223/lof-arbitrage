from fetcher.pipeline.real_poc import build_poc_report, parse_realtime_source_payload
from fetcher.sources.realtime_poc import (
    market_symbol,
    parse_eastmoney_kline_payload,
    parse_eastmoney_push2_payload,
    parse_fundgz_payload,
    parse_sina_payload,
    parse_tencent_quote_payload,
)


def test_parse_realtime_source_payload_calculates_premium_and_metrics():
    payloads = {
        "161725": {
            "price": {"price": 1.234, "name": "招商中证白酒指数(LOF)A", "elapsed_ms": 42, "source": "unit-price"},
            "nav": {"iopv": 1.2, "elapsed_ms": 38, "source": "unit-nav"},
        },
        "161005": {
            "price": {"price": 2.0, "name": "富国天惠成长混合(LOF)A", "elapsed_ms": 60, "source": "unit-price"},
            "nav": {"iopv": None, "elapsed_ms": 25, "source": "unit-nav", "error": "missing_estimated_nav"},
        },
    }

    result = parse_realtime_source_payload(["161725", "161005"], payloads, ts="2026-06-19T10:31:00+08:00")

    assert result["ts"] == "2026-06-19T10:31:00+08:00"
    assert result["summary"] == {
        "target_count": 2,
        "ok_count": 1,
        "degraded_count": 1,
        "stale_count": 0,
        "field_completeness": 0.5,
        "elapsed_ms": 165,
    }
    ok_item = result["items"][0]
    assert ok_item["code"] == "161725"
    assert ok_item["price"] == 1.234
    assert ok_item["iopv"] == 1.2
    assert ok_item["premium"] == 0.028333
    assert ok_item["source_quality"] == "ok"
    assert ok_item["failure_reason"] == ""
    degraded_item = result["items"][1]
    assert degraded_item["code"] == "161005"
    assert degraded_item["premium"] is None
    assert degraded_item["source_quality"] == "degraded"
    assert degraded_item["failure_reason"] == "missing_estimated_nav"


def test_build_poc_report_limits_to_first_batch_codes():
    payloads = {
        code: {
            "price": {"price": 1.0, "name": code, "elapsed_ms": 1, "source": "unit-price"},
            "nav": {"iopv": 1.0, "elapsed_ms": 1, "source": "unit-nav"},
        }
        for code in ["161725", "161005", "160706", "160632", "501203", "501050"]
    }

    report = build_poc_report(payloads=payloads, ts="2026-06-19T10:31:00+08:00")

    assert [item["code"] for item in report["items"]] == ["161725", "161005", "160706", "160632", "501203"]
    assert report["summary"]["target_count"] == 5
    assert report["summary"]["ok_count"] == 5


def test_realtime_source_parsers_support_public_payloads():
    assert market_symbol("501203") == "sh501203"
    assert market_symbol("161725") == "sz161725"

    tencent = parse_tencent_quote_payload('v_sz161725="51~白酒基金LOF~161725~0.526~0.534~0.530";')
    assert tencent["name"] == "白酒基金LOF"
    assert tencent["price"] == 0.526
    assert tencent["previous_close"] == 0.534

    sina = parse_sina_payload("sz161725", 'var hq_str_sz161725="白酒LOF,1.100,1.090,1.123,1.130";')
    assert sina["name"] == "白酒LOF"
    assert sina["price"] == 1.123
    assert sina["previous_close"] == 1.09

    eastmoney = parse_eastmoney_push2_payload('{"rc":0,"data":{"f43":526,"f57":"161725","f58":"白酒基金LOF","f60":534}}')
    assert eastmoney["name"] == "白酒基金LOF"
    assert eastmoney["price"] == 0.526
    assert eastmoney["previous_close"] == 0.534

    kline = parse_eastmoney_kline_payload('{"rc":0,"data":{"code":"501203","klines":["2026-06-18 09:31,1.704","2026-06-18 09:32,1.720"]}}')
    assert kline["symbol"] == "501203"
    assert kline["price"] == 1.72
    assert kline["name"] == "501203"

    fundgz = parse_fundgz_payload('jsonpgz({"fundcode":"161725","name":"白酒LOF","jzrq":"2026-06-18","dwjz":"1.1000","gsz":"1.1200","gztime":"2026-06-19 10:31"});')
    assert fundgz["name"] == "白酒LOF"
    assert fundgz["iopv"] == 1.12
    assert fundgz["nav"] == 1.1
