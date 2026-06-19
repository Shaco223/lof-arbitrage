from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from fetcher.pipeline.real_poc import (
    build_poc_report,
    parse_realtime_source_payload,
    run_long_run,
    write_poc_outputs,
)
from fetcher.sources import realtime_poc as rp


def _build_payload(price=1.0, iopv=1.0, gztime=None, price_error=None, nav_error=None):
    price_block = {"name": "TEST", "elapsed_ms": 1, "source": "tencent_quote"}
    nav_block = {"name": "TEST", "elapsed_ms": 1, "source": "fundgz", "estimate_time": gztime or ""}
    if price_error:
        price_block.update({"error": price_error})
    else:
        price_block.update({"price": price, "previous_close": price})
    if nav_error:
        nav_block.update({"error": nav_error})
    else:
        nav_block.update({"iopv": iopv, "nav": iopv})
    return {"price": price_block, "nav": nav_block}


def test_parse_realtime_source_marks_stale_when_estimate_time_too_old():
    ts = "2026-06-19T10:35:00+08:00"
    old_gztime = "2026-06-19 10:25"
    payloads = {"161725": _build_payload(price=1.0, iopv=0.99, gztime=old_gztime)}
    result = parse_realtime_source_payload(["161725"], payloads, ts=ts, stale_threshold_seconds=300)
    item = result["items"][0]
    assert item["source_quality"] == "stale"
    assert "stale_estimated_nav" in item["failure_reason"]
    assert result["summary"]["stale_count"] == 1


def test_parse_realtime_source_keeps_ok_when_estimate_time_recent():
    ts = "2026-06-19T10:35:00+08:00"
    fresh_gztime = "2026-06-19 10:34"
    payloads = {"161725": _build_payload(price=1.0, iopv=0.99, gztime=fresh_gztime)}
    result = parse_realtime_source_payload(["161725"], payloads, ts=ts, stale_threshold_seconds=300)
    assert result["items"][0]["source_quality"] == "ok"
    assert result["summary"]["stale_count"] == 0


def test_run_long_run_writes_multi_line_jsonl(tmp_path, monkeypatch):
    snapshot = tmp_path / "snap.jsonl"
    report_dir = tmp_path / "out"

    fake_payloads = {
        code: _build_payload(price=1.0, iopv=0.99, gztime="2026-06-19 10:34")
        for code in rp.POC_CODES
    }

    def fake_build(payloads=None, ts=None, codes=None, stale_threshold_seconds=300):
        return parse_realtime_source_payload(codes or rp.POC_CODES, fake_payloads, ts=ts or "2026-06-19T10:31:00+08:00", stale_threshold_seconds=stale_threshold_seconds)

    monkeypatch.setattr("fetcher.pipeline.real_poc.build_poc_report", fake_build)

    summary = run_long_run(
        duration_minutes=0,
        interval_seconds=0,
        iterations=3,
        output_dir=report_dir,
        snapshot_file=snapshot,
        ts_start="2026-06-19T10:31:00+08:00",
        sleeper=lambda _s: None,
        now=lambda: datetime(2026, 6, 19, 10, 35, 0, tzinfo=timezone(timedelta(hours=8))),
    )

    lines = snapshot.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    parsed = [json.loads(l) for l in lines]
    assert all(len(p["items"]) == len(rp.POC_CODES) for p in parsed)
    assert summary["iterations"] == 3
    assert summary["snapshot_file"].endswith("snap.jsonl")
    assert summary["report_file"].endswith("backend-real-poc-report-v2.json")
    assert "started_at" in summary and "ended_at" in summary
    assert summary["ok_total"] == 3 * len(rp.POC_CODES)


def test_block_nav_env_makes_source_degraded(monkeypatch):
    monkeypatch.setenv("LOF_POC_BLOCK_NAV", "1")

    captured = {}

    def fake_get(self, url, *args, **kwargs):  # pragma: no cover - nav path is short-circuited
        captured["url"] = url
        raise AssertionError("client.get should not be called when nav blocked")

    client = rp.RealTimePocClient()
    try:
        result = client.fetch_estimated_nav("161725")
    finally:
        client.close()
    assert result["error"].startswith("nav_BlockedByEnv")
    assert "url" not in captured
    assert result["source"] == "fundgz"


def test_block_price_env_makes_market_price_degraded(monkeypatch):
    monkeypatch.setenv("LOF_POC_BLOCK_PRICE", "1")
    client = rp.RealTimePocClient()
    try:
        result = client.fetch_market_price("161725")
    finally:
        client.close()
    assert "BlockedByEnv" in result["error"]



def test_run_long_run_marks_stale_after_consecutive_failures(tmp_path, monkeypatch):
    from fetcher.pipeline import real_poc as rp_mod
    snapshot = tmp_path / "snap.jsonl"
    report_dir = tmp_path / "out"

    nav_blocked = _build_payload(price=1.0, iopv=None, gztime="2026-06-19 10:34", nav_error="nav_BlockedByEnv")
    fake_payloads = {code: nav_blocked for code in rp.POC_CODES}

    def fake_build(payloads=None, ts=None, codes=None, stale_threshold_seconds=86400):
        return parse_realtime_source_payload(codes or rp.POC_CODES, fake_payloads, ts=ts or "2026-06-19T10:31:00+08:00", stale_threshold_seconds=stale_threshold_seconds)

    monkeypatch.setattr(rp_mod, "build_poc_report", fake_build)

    summary = rp_mod.run_long_run(
        duration_minutes=0,
        interval_seconds=0,
        iterations=3,
        output_dir=report_dir,
        snapshot_file=snapshot,
        ts_start="2026-06-19T10:31:00+08:00",
        sleeper=lambda _s: None,
        now=lambda: datetime(2026, 6, 19, 10, 35, 0, tzinfo=timezone(timedelta(hours=8))),
    )

    rows = [json.loads(l) for l in snapshot.read_text(encoding="utf-8").strip().splitlines()]
    assert len(rows) == 3
    assert all(item["source_quality"] == "degraded" for item in rows[0]["items"])
    assert all(item["source_quality"] == "stale" for item in rows[1]["items"])
    assert all(item["source_quality"] == "stale" for item in rows[2]["items"])
    assert summary["stale_total"] == 2 * len(rp.POC_CODES)
