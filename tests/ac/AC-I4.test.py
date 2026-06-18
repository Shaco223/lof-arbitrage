"""AC-I4: ingest-realtime local M1 smoke acceptance.

Method: run dev-004 local uniCloud smoke scripts, covering bad token,
missing/invalid field, batch limit, and success ingest paths.
Pass criteria: local smoke exits 0 and covers 4010 / 4001 / 4290 / success with
accepted == submitted count.
Dependency: dev-004 local uniCloud functions and mock-unicloud.
Current status: implemented as local smoke; real deployed API regression waits
for baseURL/token.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.m1_backend import build_realtime_snapshot, run_node_smoke
from contract.prd6_contracts import INGEST_REALTIME_ITEM, assert_contract

META = AC.I4


@pytest.mark.ac_i
def test_ac_i4_ingest_payload_sample_matches_prd6_item_contract(project_root):
    assert META.code == "AC-I4"
    snapshot = build_realtime_snapshot(project_root)
    assert len(snapshot["items"]) == 30
    for item in snapshot["items"]:
        ingest_item = {key: item[key] for key in ["code", "price", "iopv", "premium", "coverage", "source_quality"]}
        assert_contract("ingest-realtime.items[]", ingest_item, INGEST_REALTIME_ITEM)


@pytest.mark.ac_i
def test_ac_i4_local_unicloud_smoke_covers_ingest_paths(project_root):
    contract = run_node_smoke(project_root, "uniCloud-aliyun/tests/contract-smoke.test.js")
    assert contract.returncode == 0, contract.stdout
    assert "contract smoke passed" in contract.stdout

    local_api = run_node_smoke(project_root, "uniCloud-aliyun/tests/local-api-smoke.test.js")
    assert local_api.returncode == 0, local_api.stdout
    assert "local api smoke passed" in local_api.stdout
