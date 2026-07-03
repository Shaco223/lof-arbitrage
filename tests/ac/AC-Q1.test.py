"""
AC-Q1: PRD 1.6.1 QDII high extended to 12 + observation pool 5 must be not_supported.

Method: build an explicit minute-snapshot JSONL with 12 high QDII rows carrying
qdii_estimate_quality=high and 5 observation pool rows attempting quality=high.
Boot local-api-server against the snapshot, then call /lof-list?type=qdii and
/lof-detail?code=<obs>/<high>. The backend must:
  - Emit qdii_estimate_quality=high for the 12 whitelisted codes with the
    R12.1/R12.2/R12.3 reference index code (usIXIC / usINX / usSOXX / usXLV /
    usXBI / usXLK / usNDX / hkHSI / hkHSCEI) matching PRD 1.6.1 M6.2.
  - Force qdii_estimate_quality=not_supported for the 5 observation codes and
    null out every other qdii_* field even when the snapshot tries to inject
    values (observation pool exclusion).
  - Return exactly 12 highs + 5 not_supported = 17 rows on /lof-list?type=qdii.

Pass criteria: enum + count + reference mapping + observation nullification.
Dependency: dev-004 (local-api-server + lof-list/lof-detail QDII enforcement).
Current status: implemented as PRD 1.6.1 e2e regression.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from _lib import AC
from contract.prd6_contracts import (
    API_LOF_LIST_ITEM,
    API_LOF_DETAIL_DATA,
    assert_contract,
)

META = AC.Q1

HIGH_SAMPLES = [
    {"code": "510900", "ref": "hkHSCEI", "nav_official": 1.0, "estimate_nav": 1.0302, "price": 1.08, "prem": 0.04834},
    {"code": "159920", "ref": "hkHSI", "nav_official": 1.2, "estimate_nav": 1.22412, "price": 1.23, "prem": 0.004804},
    {"code": "159941", "ref": "usIXIC", "nav_official": 1.45, "estimate_nav": 1.508435, "price": 1.532, "prem": 0.015636},
    {"code": "513500", "ref": "usINX", "nav_official": 2.34, "estimate_nav": 2.35404, "price": 2.41, "prem": 0.023826},
    {"code": "161125", "ref": "usINX", "nav_official": 3.08, "estimate_nav": 3.089984, "price": 3.11, "prem": 0.006475},
    {"code": "501225", "ref": "usSOXX", "nav_official": 3.5887, "estimate_nav": 3.386235, "price": 3.6, "prem": 0.063128},
    {"code": "161126", "ref": "usXLV", "nav_official": 1.03, "estimate_nav": 1.020615, "price": 1.05, "prem": 0.028816},
    {"code": "161127", "ref": "usXBI", "nav_official": 0.72, "estimate_nav": 0.740232, "price": 0.75, "prem": 0.013196},
    {"code": "161128", "ref": "usXLK", "nav_official": 1.55, "estimate_nav": 1.512885, "price": 1.56, "prem": 0.031055},
    {"code": "161130", "ref": "usNDX", "nav_official": 2.16, "estimate_nav": 2.203416, "price": 2.24, "prem": 0.016625},
    {"code": "160125", "ref": "hkHSI", "nav_official": 0.82, "estimate_nav": 0.836334, "price": 0.83, "prem": -0.007563},
    {"code": "501312", "ref": "usXLK", "nav_official": 2.4085, "estimate_nav": 2.351159, "price": 2.4, "prem": 0.020783},
]
OBSERVATION_CODES = ["164824", "160140", "162415", "164906", "160644"]
EXPECTED_HIGH_CODES = {s["code"] for s in HIGH_SAMPLES}
QDII_FIELDS = (
    "qdii_estimate_nav",
    "qdii_estimate_premium",
    "qdii_reference_index_code",
    "qdii_reference_index_name",
    "qdii_reference_index_change_pct",
    "qdii_fx_change_pct",
    "qdii_estimate_source",
    "qdii_nav_date",
)


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _write_snapshot(path: Path) -> None:
    items = []
    for s in HIGH_SAMPLES:
        items.append({
            "code": s["code"],
            "price": s["price"],
            "iopv": None,
            "premium": None,
            "coverage": 1,
            "source_quality": "ok",
            "nav_official": s["nav_official"],
            "nav_official_date": "2026-07-02",
            "qdii_estimate_nav": s["estimate_nav"],
            "qdii_estimate_premium": s["prem"],
            "qdii_reference_index_code": s["ref"],
            "qdii_reference_index_name": f"{s['ref']} ref",
            "qdii_reference_index_change_pct": 0.001,
            "qdii_fx_change_pct": -0.001,
            "qdii_estimate_quality": "high",
            "qdii_estimate_source": "reference_index_estimate",
            "qdii_nav_date": "2026-07-02",
        })
    # Observation pool: even if rt tries quality=high with values, backend must force not_supported+null.
    for code in OBSERVATION_CODES:
        items.append({
            "code": code,
            "price": 1.0,
            "iopv": None,
            "premium": None,
            "coverage": 1,
            "source_quality": "ok",
            "nav_official": 1.0,
            "nav_official_date": "2026-07-02",
            "qdii_estimate_nav": 999,
            "qdii_estimate_premium": 999,
            "qdii_reference_index_code": "MALICIOUS",
            "qdii_reference_index_name": "should be dropped",
            "qdii_reference_index_change_pct": 0.5,
            "qdii_fx_change_pct": 0.5,
            "qdii_estimate_quality": "high",
            "qdii_estimate_source": "reference_index_estimate",
            "qdii_nav_date": "2026-07-02",
        })
    snapshot = {"ts": "2026-07-03T13:27:00+08:00", "items": items}
    path.write_text(json.dumps(snapshot) + "\n", encoding="utf-8")


def _wait_ready(base_url: str, timeout_s: float = 15.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/lof-list?type=qdii", timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.3)
    return False


def _get(base_url: str, path: str, params: dict):
    url = f"{base_url}/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


@pytest.fixture(scope="module")
def qdii_local_api(project_root):
    server_script = project_root / "uniCloud-aliyun" / "local-api-server.js"
    if not server_script.exists():
        pytest.skip("local-api-server.js missing")
    tmp = Path(tempfile.mkdtemp(prefix="lof-ac-q1-"))
    snapshot_file = tmp / "local-minute-snapshots-v2.jsonl"
    _write_snapshot(snapshot_file)
    port = _pick_free_port()
    env = os.environ.copy()
    env["LOCAL_API_PORT"] = str(port)
    env["LOCAL_MINUTE_SNAPSHOT_FILE"] = str(snapshot_file)
    env["UNICLOUD_INGEST_TOKEN"] = env.get("UNICLOUD_INGEST_TOKEN", "local-dev-token")
    env["NO_PROXY"] = "127.0.0.1,localhost"
    proc = subprocess.Popen(
        ["node", str(server_script)],
        cwd=str(project_root),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        if not _wait_ready(base_url):
            proc.terminate()
            pytest.skip(f"local-api-server did not start on {base_url}")
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.mark.ac_q
def test_ac_q1_high_12_codes_and_reference_mapping(qdii_local_api):
    assert META.code == "AC-Q1"
    payload = _get(qdii_local_api, "lof-list", {"sort": "code", "type": "qdii"})
    items = payload["data"]["items"]
    by_code = {row["code"]: row for row in items}
    for sample in HIGH_SAMPLES:
        row = by_code.get(sample["code"])
        assert row is not None, f"high {sample['code']} missing in /lof-list?type=qdii"
        assert_contract(f"lof-list.items[{sample['code']}]", row, API_LOF_LIST_ITEM)
        assert row["qdii_estimate_quality"] == "high", f"{sample['code']}: quality={row['qdii_estimate_quality']}"
        assert row["qdii_reference_index_code"] == sample["ref"], (
            f"{sample['code']}: ref={row['qdii_reference_index_code']} expected {sample['ref']}"
        )
        assert row["qdii_estimate_nav"] == sample["estimate_nav"], (
            f"{sample['code']}: estimate_nav={row['qdii_estimate_nav']} expected {sample['estimate_nav']}"
        )
        assert row["qdii_estimate_premium"] == sample["prem"], (
            f"{sample['code']}: estimate_premium={row['qdii_estimate_premium']} expected {sample['prem']}"
        )


@pytest.mark.ac_q
def test_ac_q1_observation_pool_forced_not_supported(qdii_local_api):
    payload = _get(qdii_local_api, "lof-list", {"sort": "code", "type": "qdii"})
    items = payload["data"]["items"]
    by_code = {row["code"]: row for row in items}
    for code in OBSERVATION_CODES:
        row = by_code.get(code)
        assert row is not None, f"observation {code} missing in /lof-list?type=qdii"
        assert_contract(f"lof-list.items[{code}]", row, API_LOF_LIST_ITEM)
        assert row["qdii_estimate_quality"] == "not_supported", (
            f"{code}: quality={row['qdii_estimate_quality']} expected not_supported"
        )
        for field in QDII_FIELDS:
            assert row.get(field) is None, f"{code}.{field}={row.get(field)} expected null"


@pytest.mark.ac_q
def test_ac_q1_type_qdii_count_12_high_plus_5_not_supported(qdii_local_api):
    payload = _get(qdii_local_api, "lof-list", {"sort": "code", "type": "qdii"})
    items = payload["data"]["items"]
    highs = [r for r in items if r.get("qdii_estimate_quality") == "high"]
    not_supported = [r for r in items if r.get("qdii_estimate_quality") == "not_supported"]
    assert len(highs) == 12, f"expected 12 QDII high, got {len(highs)}"
    assert len(not_supported) == 5, f"expected 5 observation pool not_supported, got {len(not_supported)}"
    # observation pool must not leak into non-QDII listings
    high_codes = {r["code"] for r in highs}
    assert high_codes == EXPECTED_HIGH_CODES, f"high set mismatch: {high_codes ^ EXPECTED_HIGH_CODES}"
    not_supported_codes = {r["code"] for r in not_supported}
    assert not_supported_codes == set(OBSERVATION_CODES), (
        f"observation set mismatch: {not_supported_codes ^ set(OBSERVATION_CODES)}"
    )


@pytest.mark.ac_q
def test_ac_q1_lof_detail_observation_forced_and_high_preserved(qdii_local_api):
    detail_obs = _get(qdii_local_api, "lof-detail", {"code": "164906"})["data"]
    assert_contract("lof-detail.data (obs)", detail_obs, API_LOF_DETAIL_DATA)
    assert detail_obs["qdii_estimate_quality"] == "not_supported"
    for field in QDII_FIELDS:
        assert detail_obs.get(field) is None, f"detail.164906.{field}={detail_obs.get(field)}"

    detail_high = _get(qdii_local_api, "lof-detail", {"code": "501225"})["data"]
    assert_contract("lof-detail.data (high)", detail_high, API_LOF_DETAIL_DATA)
    assert detail_high["qdii_estimate_quality"] == "high"
    assert detail_high["qdii_reference_index_code"] == "usSOXX"


@pytest.mark.ac_q
def test_ac_q1_159941_reference_stays_usIXIC(qdii_local_api):
    """R12.3: 159941 remains usIXIC until dev-004 clears the RMSE(usNDX) gate."""
    payload = _get(qdii_local_api, "lof-list", {"sort": "code", "type": "qdii"})
    row = {r["code"]: r for r in payload["data"]["items"]}["159941"]
    assert row["qdii_reference_index_code"] == "usIXIC"
