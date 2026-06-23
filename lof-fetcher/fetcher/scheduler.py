from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo


CN_TZ = ZoneInfo("Asia/Shanghai")


def is_trading_time(moment: datetime | None = None) -> bool:
    now = moment.astimezone(CN_TZ) if moment else datetime.now(CN_TZ)
    if now.weekday() >= 5:
        return False
    current = now.time()
    return time(9, 30) <= current <= time(11, 30) or time(13, 0) <= current <= time(15, 0)


def create_scheduler(fetch_job, calibrate_job=None) -> "BlockingScheduler":
    # Imported lazily so modules that only need is_trading_time/CN_TZ (e.g. the
    # resident daemon) do not require apscheduler to be installed.
    from apscheduler.schedulers.blocking import BlockingScheduler

    from fetcher.config import get_settings

    settings = get_settings()
    scheduler = BlockingScheduler(timezone=CN_TZ)
    scheduler.add_job(fetch_job, "interval", seconds=settings.fetch_interval_seconds, id="fetch_realtime", max_instances=1)
    if calibrate_job:
        scheduler.add_job(calibrate_job, "cron", hour=18, minute=0, id="daily_calibrate", max_instances=1)
    return scheduler
