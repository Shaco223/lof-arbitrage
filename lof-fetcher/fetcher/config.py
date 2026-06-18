from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ingest_url: str = Field(default="", alias="UNICLOUD_INGEST_URL")
    ingest_token: str = Field(default="", alias="UNICLOUD_INGEST_TOKEN")
    fetch_interval_seconds: int = Field(default=60, alias="FETCH_INTERVAL_SECONDS")
    http_timeout_seconds: float = Field(default=10.0, alias="HTTP_TIMEOUT_SECONDS")
    watchlist_path: Path = Field(default=Path("../assets/lof-watchlist-v1.csv"), alias="WATCHLIST_PATH")
    benchmark_mapping_path: Path = Field(default=Path("../assets/benchmark-mapping-v1.csv"), alias="BENCHMARK_MAPPING_PATH")
    alert_premium_threshold: float = Field(default=0.05, alias="ALERT_PREMIUM_THRESHOLD")
    alert_discount_threshold: float = Field(default=-0.02, alias="ALERT_DISCOUNT_THRESHOLD")
    alert_cooldown_minutes: int = Field(default=30, alias="ALERT_COOLDOWN_MINUTES")
    source_priority: Literal["eastmoney", "sina"] = Field(default="eastmoney", alias="SOURCE_PRIORITY")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def get_settings() -> Settings:
    return Settings()
