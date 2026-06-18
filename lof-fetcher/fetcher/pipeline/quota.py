from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class QuotaBudget:
    cloud_function_calls: int = 50000
    database_reads: int = 50000
    database_writes: int = 30000


@dataclass(frozen=True)
class QuotaUsage:
    cloud_function_calls: int
    database_reads: int
    database_writes: int
    assumptions: dict[str, int]

    def within(self, budget: QuotaBudget) -> bool:
        return (
            self.cloud_function_calls <= budget.cloud_function_calls
            and self.database_reads <= budget.database_reads
            and self.database_writes <= budget.database_writes
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def estimate_daily_quota_usage(
    lof_count: int = 30,
    market_minutes: int = 240,
    frontend_daily_users: int = 20,
    list_polls_per_user: int = 120,
    detail_views_per_user: int = 20,
    history_views_per_user: int = 10,
) -> QuotaUsage:
    ingest_batches = market_minutes
    list_calls = frontend_daily_users * list_polls_per_user
    detail_calls = frontend_daily_users * detail_views_per_user
    history_calls = frontend_daily_users * history_views_per_user
    cloud_function_calls = ingest_batches + list_calls + detail_calls + history_calls

    list_reads = list_calls
    detail_reads = detail_calls * 3
    history_reads = history_calls
    database_reads = list_reads + detail_reads + history_reads
    database_writes = ingest_batches

    return QuotaUsage(
        cloud_function_calls=cloud_function_calls,
        database_reads=database_reads,
        database_writes=database_writes,
        assumptions={
            "lof_count": lof_count,
            "market_minutes": market_minutes,
            "ingest_batch_size": lof_count,
            "frontend_daily_users": frontend_daily_users,
            "list_polls_per_user": list_polls_per_user,
            "detail_views_per_user": detail_views_per_user,
            "history_views_per_user": history_views_per_user,
            "detail_reads_per_call": 3,
            "list_reads_per_call": 1,
            "history_reads_per_call": 1,
            "writes_per_ingest_batch": 1,
        },
    )


def write_quota_report(path: str | Path, usage: QuotaUsage | None = None, budget: QuotaBudget | None = None) -> Path:
    import json

    quota_usage = usage or estimate_daily_quota_usage()
    quota_budget = budget or QuotaBudget()
    payload = {
        "usage": quota_usage.to_dict(),
        "budget": asdict(quota_budget),
        "within_budget": quota_usage.within(quota_budget),
        "notes": [
            "AC-S1 hard gate still requires 3 real trading days of uniCloud evidence before release.",
            "Local estimate counts 30 LOF as one ingest request and one batch database write per market minute.",
            "list/detail/history reads are estimated by function path, not by paid cloud export.",
        ],
    }
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output
