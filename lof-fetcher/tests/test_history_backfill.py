from fetcher.sources.history import (
    parse_eastmoney_kline,
    parse_lsjz,
    parse_tencent_kline,
)
from fetcher.pipeline.history_backfill import (
    build_history_records,
    compute_premium_pctile,
    load_history_file,
    merge_records,
    recompute_series,
    save_history_file,
)


def test_parse_eastmoney_kline_extracts_date_close():
    text = '{"data": {"klines": ["2026-06-22,0.527", "2026-06-23,0.520"]}}'
    out = parse_eastmoney_kline(text)
    assert out == {"2026-06-22": 0.527, "2026-06-23": 0.520}


def test_parse_tencent_kline_extracts_close_from_qfqday():
    symbol = "sz161725"
    text = (
        '{"data": {"' + symbol + '": {"qfqday": '
        '[["2026-06-22","0.52","0.527","0.53","0.51","100"]]}}}'
    )
    out = parse_tencent_kline(symbol, text)
    assert out == {"2026-06-22": 0.527}


def test_parse_lsjz_extracts_unit_nav():
    text = '{"Data": {"LSJZList": [{"FSRQ": "2026-06-22", "DWJZ": "0.5289"}]}}'
    out = parse_lsjz(text)
    assert out == {"2026-06-22": 0.5289}


def test_build_history_records_premium_and_insufficient_pctile():
    closes = {"2026-06-22": 0.527, "2026-06-23": 0.520}
    navs = {"2026-06-22": 0.5289}
    rows = build_history_records("161725", closes, navs)
    by_date = {r["date"]: r for r in rows}
    # premium_close = close/nav - 1, rounded to 6
    assert by_date["2026-06-22"]["premium_close"] == round(0.527 / 0.5289 - 1, 6)
    # NAV missing (T+1 not yet published) -> premium_close / pctile stay None
    assert by_date["2026-06-23"]["official_nav"] is None
    assert by_date["2026-06-23"]["premium_close"] is None
    # Fewer than 30 valid trading days -> percentile must be None (no fallback)
    assert all(r["premium_pctile_30d"] is None for r in rows)


def test_compute_premium_pctile_full_window():
    premiums = [i / 1000.0 for i in range(30)]
    # current is the max in window -> percentile 1.0
    assert compute_premium_pctile(premiums, 29, window=30) == 1.0
    # one short of the window -> None
    assert compute_premium_pctile(premiums, 28, window=30) is None


def test_merge_records_never_overwrites_confirmed_nav_with_null():
    existing = [{"code": "161725", "date": "2026-06-22", "close_price": 0.527,
                 "official_nav": 0.5289}]
    incoming = [{"code": "161725", "date": "2026-06-22", "close_price": 0.528,
                 "official_nav": None}]
    merged = merge_records(existing, incoming)
    row = next(r for r in merged if r["date"] == "2026-06-22")
    # close_price updated, confirmed NAV preserved (not nulled)
    assert row["close_price"] == 0.528
    assert row["official_nav"] == 0.5289


def test_save_then_load_roundtrip_and_recompute(tmp_path):
    rows = [
        {"code": "161725", "date": "2026-06-22", "close_price": 0.527, "official_nav": 0.5289},
        {"code": "161725", "date": "2026-06-23", "close_price": 0.520, "official_nav": None},
    ]
    rows = recompute_series(rows)
    path = tmp_path / "hist.jsonl"
    save_history_file(path, rows)
    loaded = load_history_file(path)
    assert len(loaded) == 2
    assert {r["date"] for r in loaded} == {"2026-06-22", "2026-06-23"}
    confirmed = next(r for r in loaded if r["date"] == "2026-06-22")
    assert confirmed["premium_close"] == round(0.527 / 0.5289 - 1, 6)
