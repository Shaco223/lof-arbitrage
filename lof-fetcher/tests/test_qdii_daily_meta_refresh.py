
from __future__ import annotations

import json
from pathlib import Path

from fetcher.pipeline.shares_confirm_refresh import update_sample_dataset_shares_confirm
from fetcher.pipeline.subscribe_refresh import update_sample_dataset_subscribe_status


def _write_dataset(path: Path) -> None:
    path.write_text(json.dumps({"lof_meta": [], "lof_realtime": [], "lof_history": [], "lof_holdings": []}), encoding="utf-8")


def test_subscribe_refresh_upserts_qdii_watchlist_meta(tmp_path):
    dataset = tmp_path / "sample.json"
    _write_dataset(dataset)

    updated = update_sample_dataset_subscribe_status(
        {
            "159920": {
                "subscribe_status": "suspended",
                "redeem_status": "suspended",
                "subscribe_limit_amount": None,
                "subscribe_limit_period": None,
            }
        },
        dataset,
    )

    data = json.loads(dataset.read_text(encoding="utf-8"))
    row = next(item for item in data["lof_meta"] if item["code"] == "159920")
    assert updated == 1
    assert row["name"] == "\u6052\u751fETF"
    assert row["type"] == "qdii"
    assert row["subscribe_status"] == "suspended"


def test_shares_refresh_upserts_qdii_watchlist_meta(tmp_path):
    dataset = tmp_path / "sample.json"
    _write_dataset(dataset)

    updated = update_sample_dataset_shares_confirm(
        {
            "159920": {
                "shares_onexchange": 640756.0,
                "shares_incr_daily": 12.0,
                "purchase_confirm_day": None,
                "redeem_confirm_day": None,
            }
        },
        dataset,
    )

    data = json.loads(dataset.read_text(encoding="utf-8"))
    row = next(item for item in data["lof_meta"] if item["code"] == "159920")
    assert updated == 1
    assert row["name"] == "\u6052\u751fETF"
    assert row["type"] == "qdii"
    assert row["shares_onexchange"] == 640756.0
    assert row["shares_incr_daily"] == 12.0
