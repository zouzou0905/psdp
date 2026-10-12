from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "AI Product Operations Platform API"
    app_env: Literal["local", "test", "staging", "production", "experiment"] = "local"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://app:change-me@localhost:5432/ai_product_ops"
    database_echo: bool = False
    database_pool_size: int = Field(default=5, ge=1)
    database_max_overflow: int = Field(default=10, ge=0)
    database_connect_timeout_seconds: float = Field(default=5.0, gt=0)
    cors_origins: list[str] = ["http://localhost:3001"]
    log_level: str = "INFO"
    auth_secret_key: SecretStr | None = None
    auth_session_ttl_minutes: int = Field(default=30, ge=5, le=1440)
    auth_issuer: str = "ai-product-operations-platform"
    auth_audience: str = "ai-product-operations-api"
    auth_cookie_samesite: Literal["lax", "strict"] = "lax"
    demo_operations_password: SecretStr | None = None
    demo_procurement_password: SecretStr | None = None
    demo_creative_password: SecretStr | None = None
    demo_admin_password: SecretStr | None = None
    deepseek_api_key: SecretStr | None = None
    deepseek_base_url: SecretStr = SecretStr("https://api.deepseek.com")
    deepseek_model: SecretStr = SecretStr("deepseek-chat")
    deepseek_connect_timeout_seconds: float = Field(default=5.0, gt=0, le=60)
    deepseek_request_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    deepseek_max_retries: int = Field(default=2, ge=0, le=5)
    export_storage_path: Path = Path("../../tmp/exports")
    export_file_ttl_hours: int = Field(default=24, ge=1, le=720)
    selection_skill_assets_path: Path = Path("../../ai/skills/amazon-selection")
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    @field_validator("auth_secret_key", mode="before")
    @classmethod
    def validate_auth_secret(cls, value: object) -> object:
        if value is None or value == "":
            return None
        raw_value = value.get_secret_value() if isinstance(value, SecretStr) else str(value)
        if len(raw_value) < 32:
            raise ValueError("AUTH_SECRET_KEY must contain at least 32 characters")
        return value

    @field_validator("export_storage_path", "selection_skill_assets_path", mode="before")
    @classmethod
    def resolve_export_storage_path(cls, value: object) -> Path:
        path = Path(str(value))
        return path if path.is_absolute() else (API_ROOT / path).resolve()

    @property
    def auth_cookie_secure(self) -> bool:
        """Session cookies are always Secure outside local/test environments."""

        return self.app_env in {"staging", "production", "experiment"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
