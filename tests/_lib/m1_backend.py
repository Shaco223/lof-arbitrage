"""Helpers for M1 backend integration acceptance tests.

The helpers use only local sample-output builders and local uniCloud smoke
scripts. They do not call paid cloud resources or live market data sources.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

DEFAULT_TS = "2026-06-18T10:31:00+08:00"


def ensure_fetcher_import(project_root: Path) -> None:
    fetcher_root = project_root / "lof-fetcher"
    if str(fetcher_root) not in sys.path:
        sys.path.insert(0, str(fetcher_root))


def build_sample_api_outputs(project_root: Path) -> dict[str, Any]:
    ensure_fetcher_import(project_root)
    from fetcher.pipeline.snapshot import build_sample_api_outputs as build_outputs

    return build_outputs(
        project_root / "assets" / "lof-watchlist-v2.csv",
        project_root / "assets" / "benchmark-mapping-v2.csv",
        DEFAULT_TS,
    )


def build_realtime_snapshot(project_root: Path) -> dict[str, Any]:
    ensure_fetcher_import(project_root)
    from fetcher.pipeline.snapshot import build_realtime_snapshot as build_snapshot

    return build_snapshot(
        project_root / "assets" / "lof-watchlist-v2.csv",
        project_root / "assets" / "benchmark-mapping-v2.csv",
        DEFAULT_TS,
    )


def run_node_smoke(project_root: Path, script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", script],
        cwd=project_root,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )


def p95_ms(samples: list[float]) -> float:
    ordered = sorted(samples)
    index = max(0, int(len(ordered) * 0.95) - 1)
    return ordered[index] * 1000


def measure_call_ms(callback: Callable[[], object], repeat: int = 100) -> float:
    durations: list[float] = []
    for _ in range(repeat):
        start = time.perf_counter()
        callback()
        durations.append(time.perf_counter() - start)
    return p95_ms(durations)

def run_ac_evidence(project_root: Path, output_dir: Path) -> dict[str, Any]:
    ensure_fetcher_import(project_root)
    from fetcher.main import main

    main(["ac-evidence", "--output-dir", str(output_dir)])
    return {
        "retry_success": read_jsonl(output_dir / "backend-ac-c2-retry-success-v2.jsonl"),
        "retry_failure": read_jsonl(output_dir / "backend-ac-c2-retry-failure-v2.jsonl"),
        "quota": json.loads((output_dir / "backend-ac-s1-quota-estimate-v2.json").read_text(encoding="utf-8")),
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
