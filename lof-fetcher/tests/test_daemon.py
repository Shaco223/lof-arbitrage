"""Tests for the resident minute-level collection daemon (PRD M2)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from fetcher.pipeline import daemon as dmod
from fetcher.sources.csv_assets import LofMeta

CN = timezone(timedelta(hours=8))


def _meta(code: str, name: str = "FUND") -> LofMeta:
    return LofMeta(code=code, name=name, type="index", scale_yi=10.0,
                   benchmark_raw=name, status="active")


def _payload(price=1.0, iopv=1.0, nav=1.0, ok=True):
    if ok:
        return {
            "price": {"price": price, "name": "TEST", "elapsed_ms": 5, "source": "tencent_quote",
                       "attempts": [{"source": "tencent_quote", "elapsed_ms": 5, "hit": True}]},
            "nav": {"iopv": iopv, "nav": nav, "elapsed_ms": 5, "source": "fundgz",
                     "estimate_time": "2026-06-22 10:34",
                     "attempts": [{"source": "fundgz", "elapsed_ms": 5, "hit": True}]},
        }
    return {
        "price": {"price": None, "elapsed_ms": 5, "source": "tencent_quote", "error": "ConnectError"},
        "nav": {"iopv": None, "elapsed_ms": 5, "source": "fundgz", "error": "missing_estimated_nav"},
    }


def test_daemon_collects_every_tick_during_trading_hours(tmp_path):
    metas = [_meta("161725"), _meta("161005")]
    snap = tmp_path / "snap.jsonl"

    def provider(_metas):
        return {m.code: _payload() for m in _metas}

    summary = dmod.run_daemon(
        metas=metas,
        output_dir=tmp_path,
        snapshot_file=snap,
        with_holdings=False,
        max_iterations=3,
        trading_interval_seconds=0,
        sleeper=lambda _s: None,
        now=lambda: datetime(2026, 6, 22, 10, 0, 0, tzinfo=CN),
        trading_check=lambda _m: True,
        payload_provider=provider,
    )
    assert summary["collect_iterations"] == 3
    assert summary["idle_iterations"] == 0
    assert summary["error_iterations"] == 0
    rows = [json.loads(l) for l in snap.read_text(encoding="utf-8").strip().splitlines()]
    assert len(rows) == 3
    assert all(set(r["items"][0].keys()) == {
        "code", "price", "price_change_pct", "volume_amount",
        "iopv", "premium", "coverage", "source_quality",
        "nav_official", "nav_official_date",
    } for r in rows)


def test_daemon_sleeps_and_does_not_collect_outside_trading_hours(tmp_path):
    metas = [_meta("161725")]
    snap = tmp_path / "snap.jsonl"
    calls = {"provider": 0}

    def provider(_metas):
        calls["provider"] += 1
        return {m.code: _payload() for m in _metas}

    summary = dmod.run_daemon(
        metas=metas,
        output_dir=tmp_path,
        snapshot_file=snap,
        with_holdings=False,
        max_iterations=2,
        idle_interval_seconds=0,
        sleeper=lambda _s: None,
        now=lambda: datetime(2026, 6, 22, 20, 0, 0, tzinfo=CN),  # after close
        trading_check=lambda _m: False,
        payload_provider=provider,
    )
    assert summary["idle_iterations"] == 2
    assert summary["collect_iterations"] == 0
    assert calls["provider"] == 0  # no source consumed when idle
    assert not snap.exists()


def test_daemon_single_lof_failure_does_not_break_others(tmp_path):
    metas = [_meta("161725"), _meta("161005")]
    snap = tmp_path / "snap.jsonl"

    def provider(_metas):
        return {"161725": _payload(ok=True), "161005": _payload(ok=False)}

    summary = dmod.run_daemon(
        metas=metas,
        output_dir=tmp_path,
        snapshot_file=snap,
        with_holdings=False,
        max_iterations=1,
        trading_interval_seconds=0,
        sleeper=lambda _s: None,
        now=lambda: datetime(2026, 6, 22, 10, 0, 0, tzinfo=CN),
        trading_check=lambda _m: True,
        payload_provider=provider,
    )
    assert summary["collect_iterations"] == 1
    assert summary["last_summary"]["ok_count"] == 1
    assert summary["last_summary"]["degraded_count"] == 1


def test_daemon_two_consecutive_failures_escalate_to_stale(tmp_path):
    metas = [_meta("161005")]
    snap = tmp_path / "snap.jsonl"

    def provider(_metas):
        return {"161005": _payload(ok=False)}

    summary = dmod.run_daemon(
        metas=metas,
        output_dir=tmp_path,
        snapshot_file=snap,
        with_holdings=False,
        max_iterations=2,
        trading_interval_seconds=0,
        sleeper=lambda _s: None,
        now=lambda: datetime(2026, 6, 22, 10, 0, 0, tzinfo=CN),
        trading_check=lambda _m: True,
        payload_provider=provider,
    )
    rows = [json.loads(l) for l in snap.read_text(encoding="utf-8").strip().splitlines()]
    assert rows[0]["items"][0]["source_quality"] == "degraded"
    assert rows[1]["items"][0]["source_quality"] == "stale"


def test_daemon_iteration_exception_is_caught_and_loop_continues(tmp_path):
    metas = [_meta("161725")]
    snap = tmp_path / "snap.jsonl"
    state = {"n": 0}

    def flaky_provider(_metas):
        state["n"] += 1
        if state["n"] == 1:
            raise RuntimeError("boom")
        return {m.code: _payload() for m in _metas}

    summary = dmod.run_daemon(
        metas=metas,
        output_dir=tmp_path,
        snapshot_file=snap,
        with_holdings=False,
        max_iterations=2,
        trading_interval_seconds=0,
        sleeper=lambda _s: None,
        now=lambda: datetime(2026, 6, 22, 10, 0, 0, tzinfo=CN),
        trading_check=lambda _m: True,
        payload_provider=flaky_provider,
    )
    assert summary["error_iterations"] == 1
    assert summary["collect_iterations"] == 1  # second tick recovered



def test_daemon_sediments_close_estimate_on_trading_to_idle_transition(tmp_path):
    # PRD 1.2.3: on the trading -> non-trading transition (market close), the
    # daemon appends the day's premium (close-time price/IOPV-1) as
    # premium_estimate_close into the history JSONL exactly once.
    metas = [_meta("161725")]
    snap = tmp_path / "snap.jsonl"
    hist = tmp_path / "hist.jsonl"
    states = iter([True, True, False])  # 2 trading ticks, then close transition

    def provider(_metas):
        # price=1.05, iopv=1.0 -> premium = 0.05 (the close-time estimate)
        return {m.code: _payload(price=1.05, iopv=1.0, nav=1.0) for m in _metas}

    dmod.run_daemon(
        metas=metas,
        output_dir=tmp_path,
        snapshot_file=snap,
        history_file=hist,
        with_holdings=False,
        max_iterations=3,
        trading_interval_seconds=0,
        idle_interval_seconds=0,
        sleeper=lambda _s: None,
        now=lambda: datetime(2026, 6, 22, 15, 0, 0, tzinfo=CN),
        trading_check=lambda _m: next(states),
        payload_provider=provider,
        pid_file=None,
        stop_file=None,
        log_file=None,
        enforce_singleton=False,
    )
    rows = [json.loads(l) for l in hist.read_text(encoding="utf-8").strip().splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["code"] == "161725"
    assert row["date"] == "2026-06-22"
    assert row["premium_estimate_close"] == 0.05
    # official_nav not backfilled yet -> premium_close + deviation null (T+1 pending)
    assert row["premium_close"] is None
    assert row["premium_deviation"] is None
