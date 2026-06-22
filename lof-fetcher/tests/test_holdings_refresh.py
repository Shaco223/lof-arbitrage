from __future__ import annotations

from fetcher.pipeline.holdings_refresh import build_holdings_payload, round6
from fetcher.sources.csv_assets import LofMeta
from fetcher.sources.holdings import HoldingRow, parse_jjcc_html, stock_suffix
from fetcher.sources.stock_quote import tencent_symbol


SAMPLE_HTML = (
    "var apidata={ content:\"<h4><label class='right'>截止至：<font class='px12'>2026-03-31</font></label></h4>"
    "<table><tbody>"
    "<tr><td>1</td><td><a href='x'>600519</a></td><td class='tol'><a href='x'>贵州茅台</a></td>"
    "<td class='tor'><span></span></td><td class='tor'><span></span></td>"
    "<td class='xglj'><a>变动</a></td><td class='tor'>18.33%</td><td class='tor'>508.34</td></tr>"
    "<tr><td>2</td><td><a href='x'>000858</a></td><td class='tol'><a href='x'>五粮液</a></td>"
    "<td class='tor'><span></span></td><td class='tor'><span></span></td>"
    "<td class='xglj'><a>变动</a></td><td class='tor'>16.14%</td><td class='tor'>120.0</td></tr>"
    "</tbody></table>\",arryear:[]};"
)


def test_stock_suffix():
    assert stock_suffix("600519") == "600519.SH"
    assert stock_suffix("000858") == "000858.SZ"
    assert stock_suffix("300750") == "300750.SZ"
    assert stock_suffix("900001") == "900001.SH"


def test_tencent_symbol():
    assert tencent_symbol("600519.SH") == "sh600519"
    assert tencent_symbol("000858.SZ") == "sz000858"
    assert tencent_symbol("300750") == "sz300750"


def test_parse_jjcc_html():
    report_date, rows = parse_jjcc_html(SAMPLE_HTML)
    assert report_date == "2026-03-31"
    assert len(rows) == 2
    assert rows[0].stock_code == "600519.SH"
    assert rows[0].stock_name == "贵州茅台"
    assert abs(rows[0].weight - 0.1833) < 1e-9
    assert rows[0].report_date == "2026-03-31"


def test_build_holdings_payload_degrades(monkeypatch):
    metas = [
        LofMeta(code="161725", name="白酒", type="index", scale_yi=300, benchmark_raw="", status="active"),
        LofMeta(code="501311", name="港股通", type="index", scale_yi=4, benchmark_raw="", status="active_low_liquidity"),
    ]

    class FakeHoldingsClient:
        def __init__(self, *a, **k):
            pass

        def fetch_holdings(self, code, topline=10):
            from fetcher.sources.holdings import HoldingsResult
            if code == "161725":
                return HoldingsResult(
                    code=code,
                    report_date="2026-03-31",
                    rows=[HoldingRow("600519.SH", "贵州茅台", 0.18, "2026-03-31")],
                )
            return HoldingsResult(code=code, report_date="2026-03-31", rows=[], error="empty_holdings")

        def close(self):
            pass

    class FakeQuoteClient:
        def __init__(self, *a, **k):
            pass

        def fetch_change_pct(self, codes):
            return {"600519.SH": 0.02}

        def close(self):
            pass

    monkeypatch.setattr("fetcher.pipeline.holdings_refresh.HoldingsClient", FakeHoldingsClient)
    monkeypatch.setattr("fetcher.pipeline.holdings_refresh.StockQuoteClient", FakeQuoteClient)

    payload = build_holdings_payload(metas, ts="2026-06-22T13:00:00+08:00")
    assert payload["summary"]["fetched_count"] == 1
    assert payload["summary"]["missing_count"] == 1
    assert len(payload["holdings"]) == 1
    row = payload["holdings"][0]
    assert row["stock_code"] == "600519.SH"
    assert row["price_change_pct"] == 0.02
    assert row["contribution_pct"] == round6(0.18 * 0.02)


def test_build_holdings_payload_null_when_no_realtime(monkeypatch):
    metas = [LofMeta(code="161725", name="白酒", type="index", scale_yi=300, benchmark_raw="", status="active")]

    class FakeHoldingsClient:
        def __init__(self, *a, **k):
            pass

        def fetch_holdings(self, code, topline=10):
            from fetcher.sources.holdings import HoldingsResult
            return HoldingsResult(
                code=code,
                report_date="2026-03-31",
                rows=[HoldingRow("600519.SH", "贵州茅台", 0.18, "2026-03-31")],
            )

        def close(self):
            pass

    monkeypatch.setattr("fetcher.pipeline.holdings_refresh.HoldingsClient", FakeHoldingsClient)
    payload = build_holdings_payload(metas, ts="t", with_realtime=False)
    row = payload["holdings"][0]
    assert row["price_change_pct"] is None
    assert row["contribution_pct"] is None
