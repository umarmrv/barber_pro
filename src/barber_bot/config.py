from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")

    bot_token: str = Field(alias="BOT_TOKEN")
    webhook_secret: str = Field(alias="WEBHOOK_SECRET")
    webhook_url: str | None = Field(default=None, alias="WEBHOOK_URL")
    admin_api_secret: str = Field(default="", alias="ADMIN_API_SECRET")

    postgres_dsn: str = Field(alias="POSTGRES_DSN")
    postgres_dsn_sync: str | None = Field(default=None, alias="POSTGRES_DSN_SYNC")
    redis_dsn: str = Field(alias="REDIS_DSN")

    salon_timezone: str = Field(default="Asia/Tashkent", alias="SALON_TIMEZONE")
    default_region: str = Field(default="TJ", alias="DEFAULT_REGION")
    default_locale: str = Field(default="ru", alias="DEFAULT_LOCALE")

    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS")
    admin_group_id: int | None = Field(default=None, alias="ADMIN_GROUP_ID")

    booking_min_lead_hours: int = Field(default=1, alias="BOOKING_MIN_LEAD_HOURS")
    booking_max_days: int = Field(default=14, alias="BOOKING_MAX_DAYS")
    cancel_min_lead_hours: int = Field(default=2, alias="CANCEL_MIN_LEAD_HOURS")

    reminder_poll_seconds: int = Field(default=30, alias="REMINDER_POLL_SECONDS")
    idempotency_ttl_seconds: int = Field(default=86400, alias="IDEMPOTENCY_TTL_SECONDS")
    draft_ttl_seconds: int = Field(default=900, alias="DRAFT_TTL_SECONDS")

    auto_create_schema: bool = Field(default=False, alias="AUTO_CREATE_SCHEMA")
    skip_bot_api_calls: bool = Field(default=False, alias="SKIP_BOT_API_CALLS")

    @property
    def admin_ids(self) -> set[int]:
        return set(_parse_admin_ids(self.admin_ids_raw))


def _parse_admin_ids(raw: str) -> Iterable[int]:
    if not raw.strip():
        return []
    ids: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        ids.append(int(part))
    return ids


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
