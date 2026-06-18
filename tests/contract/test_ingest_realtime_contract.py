"""PRD §6.4 ingest-realtime static contract."""
from __future__ import annotations

import pytest

from contract.prd6_contracts import (
    COMMON_ERROR_CODES,
    COMMON_RESPONSE,
    INGEST_REALTIME_BODY,
    INGEST_REALTIME_DATA,
    INGEST_REALTIME_ERROR_CODES,
    INGEST_REALTIME_HEADER,
    INGEST_REALTIME_ITEM,
    INGEST_REALTIME_REQUEST_SAMPLE,
    INGEST_REALTIME_RESPONSE_SAMPLE,
    assert_contract,
)


@pytest.mark.contract
def test_ingest_realtime_request_matches_prd6_contract():
    request = INGEST_REALTIME_REQUEST_SAMPLE
    assert_contract("ingest-realtime.headers", request["headers"], INGEST_REALTIME_HEADER)
    assert_contract("ingest-realtime.body", request["body"], INGEST_REALTIME_BODY)
    assert request["body"]["items"], "ingest-realtime.body.items should include submitted rows"
    for item in request["body"]["items"]:
        assert_contract("ingest-realtime.body.items[]", item, INGEST_REALTIME_ITEM)


@pytest.mark.contract
def test_ingest_realtime_success_response_matches_prd6_contract():
    response = INGEST_REALTIME_RESPONSE_SAMPLE
    assert_contract("ingest-realtime.response", response, COMMON_RESPONSE)
    assert_contract("ingest-realtime.data", response["data"], INGEST_REALTIME_DATA)
    assert response["data"]["accepted"] >= 0
    assert response["data"]["rejected"] >= 0


@pytest.mark.contract
def test_ingest_realtime_error_codes_are_declared_in_common_prd6_errors():
    assert INGEST_REALTIME_ERROR_CODES <= COMMON_ERROR_CODES
