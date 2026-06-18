"""Local real API e2e acceptance tests.

By default these tests target the local real API service at 127.0.0.1:8787.
Online uniCloud endpoints are skipped unless ALLOW_ONLINE_REAL_API=1 is set by
the project manager for a low-frequency smoke run.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Any

import pytest

from contract.prd6_contracts import (
    API_LOF_DETAIL_DATA,
    API_LOF_DETAIL_REQUIRED_BLOCKS,
    API_LOF_HISTORY_DATA,
    API_LOF_LIST_DATA,
    API_LOF_LIST_ITEM,
    COMMON_RESPONSE,
    COVERAGE_BREAKDOWN,
    HISTORY_ITEM,
    INGEST_REALTIME_DATA,
    REALTIME_BLOCK,
    assert_contract,
)

DEFAULT_LOCAL_API_BASE = "http://127.0.0.1:8787"
REAL_API_BASE = os.getenv("REAL_API_BASE", DEFAULT_LOCAL_API_BASE).rstrip("/")
FN_LIST = os.getenv("REAL_API_FN_LIST", "lof-list")
FN_DETAIL = os.getenv("REAL_API_FN_DETAIL", "lof-detail")
FN_HISTORY = os.getenv("REAL_API_FN_HISTORY", "lof-history")
FN_INGEST = os.getenv("REAL_API_FN_INGEST", "lof-ingest")
P95_REPEAT = int(os.getenv("REAL_API_P95_REPEAT", "20"))
ALLOW_ONLINE_REAL_API = os.getenv("ALLOW_ONLINE_REAL_API") == "1"

pytestmark = pytest.mark.skipif(
    "next.bspapp.com" in REAL_API_BASE and not ALLOW_ONLINE_REAL_API,
    reason="online uniCloud smoke requires ALLOW_ONLINE_REAL_API=1",
)


def call_api(fn: str, query: dict[str, Any] | None = None, method: str = "GET", body: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[dict[str, Any], float, int]:
    url = f"{REAL_API_BASE}/{fn}"
    if query:
        url += "?" + urllib.parse.urlencode({key: value for key, value in query.items() if value is not None})
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    elapsed_ms = (time.perf_counter() - start) * 1000
    return json.loads(raw), elapsed_ms, status


def percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    index = max(0, int(len(ordered) * 0.95) - 1)
    return ordered[index]


def is_local_api_base() -> bool:
    host = urllib.parse.urlparse(REAL_API_BASE).hostname
    return host in {"127.0.0.1", "::1", "localhost"}


def is_deprecated_localhost_base() -> bool:
    return urllib.parse.urlparse(REAL_API_BASE).hostname == "localhost"


@lru_cache(maxsize=1)
def local_api_available() -> bool:
    try:
        call_api(FN_LIST, {"sort": "code"})
        return True
    except (OSError, TimeoutError, urllib.error.URLError):
        return False


@pytest.fixture(scope="session", autouse=True)
def require_real_api_available() -> None:
    if is_deprecated_localhost_base():
        pytest.fail("localhost:8787 is not an acceptance base URL; use http://127.0.0.1:8787")
    if is_local_api_base() and not local_api_available():
        pytest.skip(f"local real API not available at {REAL_API_BASE}")


@pytest.fixture(scope="session")
def real_list_response() -> dict[str, Any]:
    payload, _, status = call_api(FN_LIST, {"sort": "code"})
    assert status == 200
    return payload


@pytest.fixture(scope="session")
def sample_code(real_list_response: dict[str, Any]) -> str:
    return real_list_response["data"]["items"][0]["code"]


@pytest.mark.ac_i
def test_real_api_ac_i1_list_contract_and_p95(real_list_response: dict[str, Any]) -> None:
    assert_contract("real.lof-list.response", real_list_response, COMMON_RESPONSE)
    assert_contract("real.lof-list.data", real_list_response["data"], API_LOF_LIST_DATA)
    items = real_list_response["data"]["items"]
    assert len(items) == 30
    for item in items:
        assert_contract("real.lof-list.data.items[]", item, API_LOF_LIST_ITEM)

    timings = [call_api(FN_LIST, {"sort": "code"})[1] for _ in range(P95_REPEAT)]
    assert percentile_95(timings) <= 800


@pytest.mark.ac_i
def test_real_api_ac_i2_detail_contract(sample_code: str) -> None:
    payload, _, status = call_api(FN_DETAIL, {"code": sample_code})
    assert status == 200
    data = payload["data"]
    assert_contract("real.lof-detail.response", payload, COMMON_RESPONSE)
    assert_contract("real.lof-detail.data", data, API_LOF_DETAIL_DATA)
    assert API_LOF_DETAIL_REQUIRED_BLOCKS <= set(data)
    assert_contract("real.lof-detail.coverage_breakdown", data["coverage_breakdown"], COVERAGE_BREAKDOWN)
    assert_contract("real.lof-detail.realtime", data["realtime"], REALTIME_BLOCK)


@pytest.mark.ac_i
def test_real_api_ac_i3_history_contract(sample_code: str) -> None:
    payload, _, status = call_api(FN_HISTORY, {"code": sample_code, "days": 30})
    assert status == 200
    data = payload["data"]
    assert_contract("real.lof-history.response", payload, COMMON_RESPONSE)
    assert_contract("real.lof-history.data", data, API_LOF_HISTORY_DATA)
    assert data["granularity"] == "day"
    assert len(data["items"]) >= 20
    for item in data["items"]:
        assert_contract("real.lof-history.data.items[]", item, HISTORY_ITEM)


@pytest.mark.ac_i
def test_real_api_ac_i4_ingest_rejects_missing_token() -> None:
    payload, _, status = call_api(FN_INGEST, method="POST", body={"ts": "2026-06-18T10:31:00+08:00", "items": []})
    assert status == 200
    assert payload["code"] == 4010


@pytest.mark.ac_i
@pytest.mark.skipif(not os.getenv("REAL_API_INGEST_TOKEN"), reason="REAL_API_INGEST_TOKEN not configured")
def test_real_api_ac_i4_ingest_positive_private_token(project_root) -> None:
    import sys

    fetcher_root = project_root / "lof-fetcher"
    if str(fetcher_root) not in sys.path:
        sys.path.insert(0, str(fetcher_root))
    from fetcher.pipeline.snapshot import build_realtime_snapshot

    snapshot = build_realtime_snapshot(
        project_root / "assets" / "lof-watchlist-v2.csv",
        project_root / "assets" / "benchmark-mapping-v2.csv",
        "2026-06-18T10:31:00+08:00",
    )
    body = {"ts": snapshot["ts"], "items": [{key: item[key] for key in ["code", "price", "iopv", "premium", "coverage", "source_quality"]} for item in snapshot["items"]]}
    payload, _, status = call_api(FN_INGEST, method="POST", body=body, headers={"X-Ingest-Token": os.environ["REAL_API_INGEST_TOKEN"]})
    assert status == 200
    assert_contract("real.lof-ingest.response", payload, COMMON_RESPONSE)
    assert_contract("real.lof-ingest.data", payload["data"], INGEST_REALTIME_DATA)
    assert payload["data"]["accepted"] == len(body["items"])
    assert payload["data"]["rejected"] == 0
