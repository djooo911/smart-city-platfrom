"""
Application configuration.

Centralizes all environment-driven settings using pydantic-settings so that
no other module in the codebase reads os.environ directly. This keeps
configuration testable (settings can be overridden in tests) and makes the
Docker/host environment the single source of truth for runtime config.

NOTE (Milestone 0 scope): this file only defines *scaffolding* settings
(app metadata, Mongo connection, logging, CORS). Domain-specific config
(anomaly thresholds, lighting curves, etc.) will be introduced in later
milestones alongside the domain logic that uses it.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General application metadata ---
    app_name: str = "Smart City Public Lighting & Traffic Monitoring API"
    app_env: str = "development"  # development | testing | production
    api_v1_prefix: str = "/api/v1"

    # --- MongoDB ---
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "smart_city_db"

    # --- Logging ---
    log_level: str = "INFO"

    # --- CORS (dashboard runs locally, on a different port) ---
    cors_allow_origins: str = "*"  # comma-separated list in real deployments

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor.

    Using lru_cache means Settings() is constructed once per process and
    reused everywhere via FastAPI's dependency injection (see api/deps.py),
    instead of re-parsing environment variables on every request.
    """
    return Settings()
