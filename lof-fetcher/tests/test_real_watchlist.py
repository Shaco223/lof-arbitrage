from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from fetcher.pipeline import real_watchlist as rw
from fetcher.pipeline.real_watchlist import (
    build_watchlist_report,
    load_default_watchlist,
    run_watchlist_long_run,
    write_watchlist_outputs,
)
from fetcher.sources.csv_assets import LofMeta


def _meta(code: str, name: str = "TEST", type_: str = "active", status: str = "active", scale: float = 10.0) -> LofMeta:
    return LofMeta(code=code, name=name, type=type_, scale_yi=scale, benchmark_raw="", status=status)


def _payload(price: float | None = 1.0, iopv: float | None = 0.99, primary: str = "tencent_quote", nav_ok: bool = True):
    if price is None:
        price_attempts = [{"source": s, "elapsed_ms": 5, "error": "Boom"} for s in ["tencent_quote", "eastmoney_kline", "eastmoney_push2", "sina"]]
        price_block: dict = {
            "source": ",".join(a["source"] for a in price_attempts),
            "elapsed_ms": 20,
            "error": ";".join(f"{a['source']}_Boom" for a in price_attempts),
            "attempts": price_attempts,
        }
    else:
        price_attempts = []
        for source in ["tencent_quote", "eastmoney_kline", "eastmoney_push2", "sina"]:
            if source == primary:
                price_attempts.append({"source": source, "elapsed_ms": 8, "hit": True})
                break
            price_attempts.append({"source": source, "elapsed_ms": 5, "error": "ConnectError"})
        price_block = {"name": "TEST", "price": price, "previous_close": price, "elapsed_ms": sum(a["elapsed_ms"] for a in price_attempts), "source": primary, "attempts": price_attempts}
    if nav_ok and iopv is not None:
        nav_block: dict = {"name": "TEST", "iopv": iopv, "nav": iopv, "elapsed_ms": 10, "source": "fundgz", "estimate_time": "2026-06-19 10:34", "attempts": [{"source": "fundgz", "elapsed_ms": 10, "hit": True}]}
    else:
        nav_block = {"source": "fundgz", "elapsed_ms": 10, "error": "nav_BlockedByEnv", "attempts": [{"source": "fundgz", "elapsed_ms": 10, "error": "BlockedByEnv"}]}
    return {"price": price_block, "nav": nav_block}


def test_load_default_watchlist_has_30_codes():
    metas = load_default_watchlist()
    assert len(metas) == 30


def test_build_watchlist_report_records_primary_source_and_completeness():
    metas = [_meta("161725"), _meta("160706"), _meta("501077", status="active_low_liquidity")]
    payloads = {
        "161725": _payload(primary="tencent_quote"),
        "160706": _payload(price=None, nav_ok=False),
        "501077": _payload(primary="sina"),
    }
    report = build_watchlist_report(metas, payloads, ts="2026-06-19T10:31:00+08:00")
    assert report["summary"]["target_count"] == 3
    assert report["summary"]["ok_count"] == 2
    assert report["summary"]["degraded_count"] == 1
    assert report["summary"]["field_completeness"] == round(2 / 3, 6)
    items_by_code = {it["code"]: it for it in report["items"]}
    assert items_by_code["161725"]["primary_price_source"] == "tencent_quote"
    assert items_by_code["161725"]["backup_price_used"] is False
    assert items_by_code["501077"]["primary_price_source"] == "sina"
    assert items_by_code["501077"]["backup_price_used"] is True
    assert items_by_code["160706"]["source_quality"] == "degraded"
    assert items_by_code["160706"]["price"] is None and items_by_code["160706"]["iopv"] is None


def test_write_watchlist_outputs_writes_section6_only_jsonl(tmp_path):
    metas = [_meta("161725")]
    payloads = {"161725": _payload(primary="tencent_quote")}
    report = build_watchlist_report(metas, payloads, ts="2026-06-19T10:31:00+08:00")
    files = write_watchlist_outputs(report, tmp_path, tmp_path / "snap.jsonl")
    snapshot = json.loads((tmp_path / "snap.jsonl").read_text(encoding="utf-8").strip())
    assert set(snapshot.keys()) == {"ts", "items"}
    assert set(snapshot["items"][0].keys()) == {"code", "price", "iopv", "premium", "coverage", "source_quality"}
    report_payload = json.loads(files["report"].read_text(encoding="utf-8"))
    assert report_payload["summary"]["target_count"] == 1


def test_run_watchlist_long_run_aggregates_stability(tmp_path, monkeypatch):
    metas = [_meta("161725"), _meta("160706"), _meta("501077", status="active_low_liquidity")]
    snapshot = tmp_path / "snap.jsonl"

    fake_payloads_per_iter = [
        {"161725": _payload(primary="tencent_quote"), "160706": _payload(primary="eastmoney_kline"), "501077": _payload(primary="sina")},
        {"161725": _payload(primary="tencent_quote"), "160706": _payload(price=None, nav_ok=False), "501077": _payload(primary="sina")},
        {"161725": _payload(primary="tencent_quote"), "160706": _payload(price=None, nav_ok=False), "501077": _payload(primary="sina")},
    ]
    counter = {"i": 0}

    def fake_provider(_metas):
        idx = counter["i"]
        counter["i"] += 1
        return fake_payloads_per_iter[idx]

    summary = run_watchlist_long_run(
        duration_minutes=0,
        interval_seconds=0,
        output_dir=tmp_path,
        snapshot_file=snapshot,
        metas=metas,
        iterations=3,
        sleeper=lambda _s: None,
        now=lambda: datetime(2026, 6, 19, 10, 35, 0, tzinfo=timezone(timedelta(hours=8))),
        payload_provider=fake_provider,
        ts_start="2026-06-19T10:31:00+08:00",
    )

    rows = [json.loads(l) for l in snapshot.read_text(encoding="utf-8").strip().splitlines()]
    assert len(rows) == 3
    assert all(len(r["items"]) == 3 for r in rows)

    stability = json.loads((tmp_path / "backend-real-watchlist-stability-v2.json").read_text(encoding="utf-8"))
    items_by_code = {it["code"]: it for it in stability["items"]}
    assert items_by_code["161725"]["recommendation"] == "keep"
    assert items_by_code["161725"]["ok_ratio"] == 1.0
    assert items_by_code["160706"]["recommendation"] == "replace"
    assert items_by_code["160706"]["stale"] >= 1
    md = (tmp_path / "backend-real-watchlist-stability-v2.md").read_text(encoding="utf-8")
    assert "30 只 watchlist-v2 长跑稳定性结论" in md
    assert "keep" in md and "replace" in md
    assert summary["target_count"] == 3
    assert summary["iterations"] == 3
    assert summary["stability_md"].endswith("backend-real-watchlist-stability-v2.md")
    assert summary["last_summary"]["target_count"] == 3
