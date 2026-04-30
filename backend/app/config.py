from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "dev"
    debug: bool = True
    secret_key: str = "dev-only-change-me-please-32-bytes-min"

    jwt_algorithm: str = "HS256"
    jwt_ttl_minutes: int = 60 * 24 * 7
    cookie_secure: bool = False
    cookie_domain: str | None = None
    cookie_name: str = "access_token"

    database_url: str = "sqlite+aiosqlite:///./dev.db"

    public_base_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"

    amadeus_client_id: str | None = None
    amadeus_client_secret: str | None = None
    amadeus_hostname: str = "test"
    amadeus_default_currency: str = "USD"
    serpapi_key: str | None = None
    default_flight_provider: str = "amadeus"

    scheduler_enabled: bool = False
    price_refresh_interval_minutes: int = 360
    price_change_threshold_pct: float = 5.0
    price_change_threshold_abs: float = 25.0

    notifier_backend: str = "console"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None

    rate_limit_public_per_minute: int = 60
    snapshot_retention_days: int = 90

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
