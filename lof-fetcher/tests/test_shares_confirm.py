"""PRD 1.4 AC-P8 / AC-P9: on-exchange shares + open-end confirm-day data source.

Pure unit tests (no network): exercise the 'T+N' normalization, the env-var-only
Cookie read (red line), and the no-source -> null fallback (AC-P8) using a stub
client. Real-coverage validation (jisilu 29/30, confirm 160216=T+2 / 501203=null)
is left to the intraday smoke documented in the runbook.
"""
from __future__ import annotations

from fetcher.sources import shares_confirm
from fetcher.sources.shares_confirm import (
    SharesConfirmClient,
    _normalize_tplusn,
    fetch_shares_confirm_map,
    get_jisilu_cookie,
)


def test_normalize_tplusn():
    assert _normalize_tplusn("T+1") == "T+1"
    assert _normalize_tplusn("T+2") == "T+2"
    assert _normalize_tplusn("T + 3 个工作日") == "T+3"
    assert _normalize_tplusn(None) is None
    assert _normalize_tplusn("--") is None
    assert _normalize_tplusn("开放") is None


def test_cookie_read_from_env_only(monkeypatch):
    monkeypatch.delenv("JISILU_COOKIE", raising=False)
    assert get_jisilu_cookie() is None
    monkeypatch.setenv("JISILU_COOKIE", "  kbz=1; user=x  ")
    assert get_jisilu_cookie() == "kbz=1; user=x"
    monkeypatch.setenv("JISILU_COOKIE", "   ")
    assert get_jisilu_cookie() is None


class _StubClient(SharesConfirmClient):
    """Stub the network calls; exercise the merge + null-fallback logic only."""

    def __init__(self, shares_map, confirm_map):
        self._shares_map = shares_map
        self._confirm_map = confirm_map

    def close(self):
        pass

    def fetch_shares_map(self):
        return self._shares_map

    def fetch_confirm_days(self, code):
        return self._confirm_map.get(code, {
            "code": code, "purchase_confirm_day": None,
            "redeem_confirm_day": None, "source": "none",
        })


def test_shares_present_and_missing_fallback_null():
    # 161725 has shares; 501311 (QDII) absent from jisilu LOF lists -> null.
    shares_map = {
        "161725": {"shares_onexchange": 361315.0, "shares_incr_daily": 63.0,
                   "shares_dt": "2026-06-24", "source": "jisilu_lof"},
    }
    confirm_map = {
        "161725": {"code": "161725", "purchase_confirm_day": "T+1",
                   "redeem_confirm_day": "T+1", "source": "eastmoney_jjfl"},
        "160216": {"code": "160216", "purchase_confirm_day": "T+2",
                   "redeem_confirm_day": "T+2", "source": "eastmoney_jjfl"},
        "501203": {"code": "501203", "purchase_confirm_day": None,
                   "redeem_confirm_day": None, "source": "none"},
    }
    client = _StubClient(shares_map, confirm_map)
    res = fetch_shares_confirm_map(["161725", "160216", "501203", "501311"], client=client)

    # Present shares.
    assert res["161725"]["shares_onexchange"] == 361315.0
    assert res["161725"]["shares_incr_daily"] == 63.0
    assert res["161725"]["purchase_confirm_day"] == "T+1"
    # 160216 confirm = T+2.
    assert res["160216"]["redeem_confirm_day"] == "T+2"
    # 501203 confirm = null (AC-P9).
    assert res["501203"]["purchase_confirm_day"] is None
    # 501311 QDII: shares null (not in jisilu LOF list) but link never crashes.
    assert res["501311"]["shares_onexchange"] is None
    assert res["501311"]["shares_incr_daily"] is None


def test_no_cookie_no_source_all_null(monkeypatch):
    # AC-P8: no Cookie + jisilu returns nothing -> shares null, no crash.
    client = _StubClient({}, {})
    res = fetch_shares_confirm_map(["161725", "501203"], client=client)
    for code in ("161725", "501203"):
        assert res[code]["shares_onexchange"] is None
        assert res[code]["shares_incr_daily"] is None



def test_qdii_shares_are_merged_from_qdii_list():
    class _QdiiStub(_StubClient):
        def fetch_qdii_shares_map(self):
            return {
                "159920": {
                    "code": "159920",
                    "shares_onexchange": 640756.0,
                    "shares_incr_daily": 12.0,
                    "shares_dt": "2026-07-02",
                    "source": "jisilu_qdii",
                }
            }

    client = _QdiiStub({}, {})
    res = fetch_shares_confirm_map(["159920"], client=client)

    assert res["159920"]["shares_onexchange"] == 640756.0
    assert res["159920"]["shares_incr_daily"] == 12.0
    assert res["159920"]["shares_source"] == "jisilu_qdii"
