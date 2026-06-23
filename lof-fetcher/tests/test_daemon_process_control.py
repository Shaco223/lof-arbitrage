# Tests for daemon process control: PID single-instance, status, stop flag, logs.
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from fetcher.pipeline import process_control as pc
from fetcher.pipeline import daemon as dmod
from fetcher.sources.csv_assets import LofMeta

CN = timezone(timedelta(hours=8))


def _meta(code: str) -> LofMeta:
    return LofMeta(code=code, name="FUND", type="index", scale_yi=10.0,
                   benchmark_raw="FUND", status="active")


def _payload():
    return {
        "price": {"price": 1.0, "name": "TEST", "elapsed_ms": 5, "source": "tencent_quote",
                   "attempts": [{"source": "tencent_quote", "elapsed_ms": 5, "hit": True}]},
        "nav": {"iopv": 1.0, "nav": 1.0, "elapsed_ms": 5, "source": "fundgz",
                 "estimate_time": "2026-06-22 10:34",
                 "attempts": [{"source": "fundgz", "elapsed_ms": 5, "hit": True}]},
    }


def test_status_reports_not_running_without_pid_file(tmp_path):
    assert pc.status(tmp_path / "daemon.pid") == {"running": False}


def test_write_and_read_pid_file_roundtrip(tmp_path):
    pid_file = tmp_path / "daemon.pid"
    info = pc.write_pid_file(pid_file, snapshot_file="snap.jsonl")
    assert info.pid == os.getpid()
    read = pc.read_pid_file(pid_file)
    assert read is not None
    assert read.pid == os.getpid()
    assert read.snapshot_file == "snap.jsonl"
    # The current process is alive and matches -> running.
    assert pc.is_running(read) is True


def test_is_running_false_on_dead_pid(tmp_path):
    pid_file = tmp_path / "daemon.pid"
    data = {"pid": 999999, "create_time": 1.0, "cmdline": "fetcher.main daemon", "started_at": "x"}
    pid_file.write_text(json.dumps(data), encoding="utf-8")
    assert pc.is_running(pc.read_pid_file(pid_file)) is False


def test_is_running_false_on_pid_reuse_create_time_mismatch(tmp_path):
    # Same live PID but a wildly different create_time => treat as a stranger.
    pid_file = tmp_path / "daemon.pid"
    data = {"pid": os.getpid(), "create_time": 1.0,
            "cmdline": "fetcher.main daemon", "started_at": "x"}
    pid_file.write_text(json.dumps(data), encoding="utf-8")
    info = pc.read_pid_file(pid_file)
    # psutil present in this env -> create_time of our process != 1.0
    if pc.psutil is not None:
        assert pc.is_running(info) is False


def test_singleton_blocks_second_start(tmp_path):
    pid_file = tmp_path / "daemon.pid"
    stop_file = tmp_path / "daemon.stop"
    # Write a pid file for the *current* process so is_running() is True.
    pc.write_pid_file(pid_file)
    with pytest.raises(RuntimeError, match="already running"):
        dmod.run_daemon(
            metas=[_meta("161725")],
            output_dir=tmp_path,
            snapshot_file=tmp_path / "snap.jsonl",
            with_holdings=False,
            max_iterations=1,
            pid_file=pid_file,
            stop_file=stop_file,
            log_file=None,
            trading_interval_seconds=0,
            sleeper=lambda _s: None,
            now=lambda: datetime(2026, 6, 22, 10, 0, 0, tzinfo=CN),
            trading_check=lambda _m: True,
            payload_provider=lambda ms: {m.code: _payload() for m in ms},
        )


def test_daemon_clears_pid_file_on_exit(tmp_path):
    pid_file = tmp_path / "daemon.pid"
    stop_file = tmp_path / "daemon.stop"
    dmod.run_daemon(
        metas=[_meta("161725")],
        output_dir=tmp_path,
        snapshot_file=tmp_path / "snap.jsonl",
        with_holdings=False,
        max_iterations=1,
        pid_file=pid_file,
        stop_file=stop_file,
        log_file=None,
        trading_interval_seconds=0,
        sleeper=lambda _s: None,
        now=lambda: datetime(2026, 6, 22, 10, 0, 0, tzinfo=CN),
        trading_check=lambda _m: True,
        payload_provider=lambda ms: {m.code: _payload() for m in ms},
    )
    assert not pid_file.exists()


def test_daemon_stops_on_stop_flag(tmp_path):
    pid_file = tmp_path / "daemon.pid"
    stop_file = tmp_path / "daemon.stop"
    # A stop flag set before start is cleared by setup, so we trip it from
    # inside the first sleep to prove the loop honors it mid-run.
    calls = {"n": 0}

    def sleeper(_s):
        calls["n"] += 1
        pc.request_stop(stop_file)  # request stop during the first sleep

    summary = dmod.run_daemon(
        metas=[_meta("161725")],
        output_dir=tmp_path,
        snapshot_file=tmp_path / "snap.jsonl",
        with_holdings=False,
        max_iterations=None,  # unbounded: only the stop flag can end it
        pid_file=pid_file,
        stop_file=stop_file,
        log_file=None,
        trading_interval_seconds=1,
        stop_poll_seconds=1,
        sleeper=sleeper,
        now=lambda: datetime(2026, 6, 22, 10, 0, 0, tzinfo=CN),
        trading_check=lambda _m: True,
        payload_provider=lambda ms: {m.code: _payload() for m in ms},
    )
    assert summary["stopped_by_flag"] is True
    assert summary["collect_iterations"] >= 1
    assert not pid_file.exists()
    assert not stop_file.exists()


def test_stop_daemon_reports_not_running_when_absent(tmp_path):
    result = pc.stop_daemon(tmp_path / "daemon.pid", tmp_path / "daemon.stop")
    assert result["stopped"] is False
    assert result["reason"] == "not_running"


def test_daemon_writes_rotating_log_file(tmp_path):
    pid_file = tmp_path / "daemon.pid"
    stop_file = tmp_path / "daemon.stop"
    log_file = tmp_path / "logs" / "daemon.log"
    dmod.run_daemon(
        metas=[_meta("161725")],
        output_dir=tmp_path,
        snapshot_file=tmp_path / "snap.jsonl",
        with_holdings=False,
        max_iterations=1,
        pid_file=pid_file,
        stop_file=stop_file,
        log_file=log_file,
        trading_interval_seconds=0,
        sleeper=lambda _s: None,
        now=lambda: datetime(2026, 6, 22, 10, 0, 0, tzinfo=CN),
        trading_check=lambda _m: True,
        payload_provider=lambda ms: {m.code: _payload() for m in ms},
    )
    assert log_file.exists()
    assert "collected" in log_file.read_text(encoding="utf-8")
