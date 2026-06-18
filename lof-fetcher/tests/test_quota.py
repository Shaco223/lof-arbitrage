from __future__ import annotations

from fetcher.pipeline.quota import QuotaBudget, estimate_daily_quota_usage


def test_quota_usage_counts_one_ingest_write_per_batch_and_frontend_reads():
    usage = estimate_daily_quota_usage(
        lof_count=30,
        market_minutes=240,
        frontend_daily_users=20,
        list_polls_per_user=120,
        detail_views_per_user=20,
        history_views_per_user=10,
    )

    assert usage.cloud_function_calls == 240 + 20 * (120 + 20 + 10)
    assert usage.database_writes == 240
    assert usage.database_reads == 20 * (120 + 20 * 3 + 10)
    assert usage.within(QuotaBudget()) is True
