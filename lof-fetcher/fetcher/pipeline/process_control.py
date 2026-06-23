# Process control for the resident daemon (go-live robustness).
#
# Provides PID-file based single-instance enforcement, status query and graceful
# stop. Designed for Windows where PIDs are reused aggressively, so we never
# trust a bare PID: a PID file also stores the process create-time and command
# line, and we verify the live process still matches before treating it as our
# daemon.
#
# A lightweight stop is implemented via a stop-flag file the daemon loop polls,
# so it works without OS-specific signals; if psutil is available we additionally
# terminate the process as a fallback.
#
# No third-party hard dependency: psutil is used opportunistically when present.
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:  # opportunistic; daemon still works without it
    import psutil  # type: ignore
except Exception:  # pragma: no cover - psutil missing fallback
    psutil = None  # type: ignore

DEFAULT_PID_FILE = Path("../outputs/daemon.pid")
DEFAULT_STOP_FILE = Path("../outputs/daemon.stop")
# Marker substrings identifying our daemon among same-named python processes.
DAEMON_CMD_MARKER = "fetcher.main"
DAEMON_CMD_MARKER2 = "daemon"


@dataclass
class PidInfo:
    pid: int
    create_time: float | None
    cmdline: str
    started_at: str
    snapshot_file: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pid": self.pid,
            "create_time": self.create_time,
            "cmdline": self.cmdline,
            "started_at": self.started_at,
            "snapshot_file": self.snapshot_file,
        }


def _now_stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _proc_create_time(pid: int) -> float | None:
    if psutil is None:
        return None
    try:
        return psutil.Process(pid).create_time()
    except Exception:
        return None


def _proc_cmdline(pid: int) -> str | None:
    if psutil is None:
        return None
    try:
        return " ".join(psutil.Process(pid).cmdline())
    except Exception:
        return None


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if psutil is not None:
        try:
            return psutil.pid_exists(pid)
        except Exception:
            return False
    # Fallback: os.kill(pid, 0) probes existence without sending a real signal.
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    except Exception:
        return False
    return True


def read_pid_file(pid_file: Path) -> PidInfo | None:
    try:
        raw = Path(pid_file).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except Exception:
        return None
    try:
        data = json.loads(raw)
    except Exception:
        # legacy / plain-int pid file
        try:
            return PidInfo(pid=int(raw.strip()), create_time=None, cmdline="", started_at="")
        except Exception:
            return None
    return PidInfo(
        pid=int(data.get("pid", 0)),
        create_time=data.get("create_time"),
        cmdline=data.get("cmdline", ""),
        started_at=data.get("started_at", ""),
        snapshot_file=data.get("snapshot_file"),
    )


def is_running(info: PidInfo | None) -> bool:
    # True only if the recorded PID is alive AND still looks like our daemon.
    # On PID reuse (Windows), create_time differs and/or cmdline no longer holds
    # our marker, so we report not-running instead of acting on a stranger pid.
    if info is None or info.pid <= 0:
        return False
    if not _pid_alive(info.pid):
        return False
    # Primary identity guard: process create-time. PID reuse on Windows always
    # yields a different create-time, so a match uniquely identifies our run.
    current_ct = _proc_create_time(info.pid)
    if info.create_time is not None and current_ct is not None:
        return abs(current_ct - info.create_time) <= 1.0
    # Fallback when create-time is unavailable (psutil missing / legacy pid
    # file): use the command-line marker to reject obviously unrelated procs.
    current_cmd = _proc_cmdline(info.pid)
    if current_cmd is not None:
        low = current_cmd.lower()
        if DAEMON_CMD_MARKER not in low and DAEMON_CMD_MARKER2 not in low:
            return False
    return True


def write_pid_file(pid_file: Path, snapshot_file: str | None = None) -> PidInfo:
    pid = os.getpid()
    info = PidInfo(
        pid=pid,
        create_time=_proc_create_time(pid),
        cmdline=_proc_cmdline(pid) or " ".join(sys.argv),
        started_at=_now_stamp(),
        snapshot_file=snapshot_file,
    )
    p = Path(pid_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(info.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return info


def clear_pid_file(pid_file: Path) -> None:
    try:
        Path(pid_file).unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass


def request_stop(stop_file: Path) -> None:
    p = Path(stop_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_now_stamp() + "\n", encoding="utf-8")


def stop_requested(stop_file: Path) -> bool:
    return Path(stop_file).exists()


def clear_stop_flag(stop_file: Path) -> None:
    try:
        Path(stop_file).unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass


def stop_daemon(pid_file: Path, stop_file: Path, *, timeout_seconds: float = 30.0,
                poll_seconds: float = 0.5) -> dict[str, Any]:
    # Gracefully stop a running daemon. Returns a result dict for the CLI.
    # Strategy: set the stop-flag file (daemon loop exits at next tick), wait up
    # to timeout; if psutil is present and the process lingers, terminate it.
    info = read_pid_file(pid_file)
    if not is_running(info):
        clear_pid_file(pid_file)
        clear_stop_flag(stop_file)
        return {"stopped": False, "reason": "not_running"}
    assert info is not None
    request_stop(stop_file)
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    while time.monotonic() < deadline:
        if not _pid_alive(info.pid):
            clear_pid_file(pid_file)
            clear_stop_flag(stop_file)
            return {"stopped": True, "pid": info.pid, "method": "stop_flag"}
        time.sleep(poll_seconds)
    # Fallback: force terminate if still alive.
    if psutil is not None and _pid_alive(info.pid):
        try:
            proc = psutil.Process(info.pid)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
            clear_pid_file(pid_file)
            clear_stop_flag(stop_file)
            return {"stopped": True, "pid": info.pid, "method": "terminate"}
        except Exception as exc:  # pragma: no cover
            return {"stopped": False, "pid": info.pid, "reason": f"terminate_failed:{exc}"}
    return {"stopped": False, "pid": info.pid, "reason": "timeout"}


def status(pid_file: Path) -> dict[str, Any]:
    info = read_pid_file(pid_file)
    running = is_running(info)
    if not running:
        return {"running": False}
    assert info is not None
    return {
        "running": True,
        "pid": info.pid,
        "started_at": info.started_at,
        "snapshot_file": info.snapshot_file,
        "cmdline": info.cmdline,
    }
