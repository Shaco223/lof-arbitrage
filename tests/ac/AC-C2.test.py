"""AC-C2: data-source failure retry acceptance.

Method: run dev-004 local AC evidence builder in a temporary directory and
validate both retry traces.
Pass criteria: the two-failure scenario succeeds on attempt 3 within 30 seconds;
the all-failure scenario records 3 attempts, ends as skipped within 30 seconds,
and never pollutes history.
Dependency: dev-004 retry trace evidence.
Current status: implemented as local evidence acceptance.
"""
from __future__ import annotations

import pytest

from _lib import AC
from _lib.m1_backend import run_ac_evidence

META = AC.C2
MAX_RETRY_SECONDS = 30
EXPECTED_SOURCE = "eastmoney"
EXPECTED_CODE = "161725"


def assert_common_retry_trace(events: list[dict[str, object]]) -> None:
    assert len(events) == 3
    assert [event["attempt"] for event in events] == [1, 2, 3]
    assert {event["source"] for event in events} == {EXPECTED_SOURCE}
    assert {event["code"] for event in events} == {EXPECTED_CODE}
    assert all(event["pollute_history"] is False for event in events)
    assert events[-1]["elapsed_seconds"] <= MAX_RETRY_SECONDS


@pytest.mark.ac_c
def test_ac_c2_retry_trace_success_and_failure_paths(project_root, tmp_path):
    assert META.code == "AC-C2"
    evidence = run_ac_evidence(project_root, tmp_path)
    success_events = evidence["retry_success"]
    failure_events = evidence["retry_failure"]

    assert_common_retry_trace(success_events)
    assert_common_retry_trace(failure_events)

    assert [event["status"] for event in success_events] == ["failed", "failed", "success"]
    assert success_events[-1]["reason"] == ""
    assert [event["status"] for event in failure_events] == ["failed", "failed", "skipped"]
    assert all(str(event["reason"]).startswith("planned source failure") for event in failure_events)
