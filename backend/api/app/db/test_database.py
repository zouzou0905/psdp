from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

from app.core.config import Settings, get_settings

_FORBIDDEN_DATABASE_NAMES = {
    "ai_product_ops_dev",
    "postgres",
    "template0",
    "template1",
}
_NON_TEST_ENVIRONMENTS = {"staging", "production"}
_NON_TEST_NAME_PATTERN = re.compile(
    r"(?:^|[_-])(?:prod|production|staging|stage)(?:$|[_-])",
    re.IGNORECASE,
)
_ACTIVE_TEST_DATABASE_URL: str | None = None


class PostgreSQLTestDatabaseSafetyError(RuntimeError):
    """Raised before a PostgreSQL integration test can touch an unsafe database."""


class PostgreSQLTestEnvironment(BaseSettings):
    """Minimal, secret-safe environment view used by the integration-test gate."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    test_database_url: SecretStr | None = None
    database_url: SecretStr | None = None
    app_env: str = "local"


@dataclass(frozen=True)
class DatabaseTarget:
    backend: str
    host: str
    port: int
    database: str

    @property
    def safe_label(self) -> str:
        return f"database '{self.database}' on host '{self.host}:{self.port}'"

    @property
    def identity(self) -> tuple[str, str, int, str]:
        return (self.backend, _normalize_host(self.host), self.port, self.database.lower())


def _normalize_host(host: str) -> str:
    normalized = host.strip().lower().strip("[]")
    if normalized in {"localhost", "::1", "0:0:0:0:0:0:0:1"}:
        return "127.0.0.1"
    return normalized


def _parse_target(raw_url: str, *, variable_name: str) -> tuple[URL, DatabaseTarget]:
    try:
        url = make_url(raw_url)
    except Exception as exc:
        raise PostgreSQLTestDatabaseSafetyError(
            f"{variable_name} is not a valid database URL"
        ) from exc

    backend = url.get_backend_name().lower()
    database = (url.database or "").strip()
    host = (url.host or "<local>").strip()
    port = url.port or 5432
    if backend != "postgresql":
        raise PostgreSQLTestDatabaseSafetyError(
            f"{variable_name} must use PostgreSQL; target host is '{host}:{port}'"
        )
    if not database:
        raise PostgreSQLTestDatabaseSafetyError(
            f"{variable_name} must include a database name; target host is '{host}:{port}'"
        )
    return url, DatabaseTarget(
        backend=backend,
        host=host,
        port=port,
        database=database,
    )


def validate_postgresql_test_database_url(
    *,
    test_database_url: str | None,
    runtime_database_url: str | None,
    app_env: str,
) -> str:
    """Return the validated test URL without ever falling back to DATABASE_URL."""

    if not test_database_url:
        raise PostgreSQLTestDatabaseSafetyError(
            "TEST_DATABASE_URL is required when PostgreSQL integration tests are enabled"
        )
    if not runtime_database_url:
        raise PostgreSQLTestDatabaseSafetyError(
            "DATABASE_URL is required only for the safety comparison; "
            "it is never used as the test URL"
        )

    _, test_target = _parse_target(
        test_database_url,
        variable_name="TEST_DATABASE_URL",
    )
    _, runtime_target = _parse_target(
        runtime_database_url,
        variable_name="DATABASE_URL",
    )

    environment = app_env.strip().lower()
    if environment in _NON_TEST_ENVIRONMENTS:
        raise PostgreSQLTestDatabaseSafetyError(
            f"PostgreSQL integration tests are forbidden when APP_ENV is '{environment}'"
        )
    test_name = test_target.database.lower()
    if test_name in _FORBIDDEN_DATABASE_NAMES:
        raise PostgreSQLTestDatabaseSafetyError(
            f"TEST_DATABASE_URL targets forbidden {test_target.safe_label}"
        )
    if not test_name.endswith("_test"):
        raise PostgreSQLTestDatabaseSafetyError(
            f"TEST_DATABASE_URL must end in '_test'; received {test_target.safe_label}"
        )
    if _NON_TEST_NAME_PATTERN.search(test_name):
        raise PostgreSQLTestDatabaseSafetyError(
            f"TEST_DATABASE_URL appears to target staging or production: {test_target.safe_label}"
        )
    if test_target.identity == runtime_target.identity:
        raise PostgreSQLTestDatabaseSafetyError(
            "TEST_DATABASE_URL must not identify the same database as DATABASE_URL: "
            f"{test_target.safe_label}"
        )
    return test_database_url


def get_postgresql_test_database_url(
    environ: Mapping[str, str] | None = None,
) -> str:
    """Load and validate the dedicated URL from environment/.env without fallback."""

    if environ is None:
        config = PostgreSQLTestEnvironment()
        test_url = (
            config.test_database_url.get_secret_value()
            if config.test_database_url is not None
            else None
        )
        runtime_url = (
            config.database_url.get_secret_value()
            if config.database_url is not None
            else None
        )
        app_env = config.app_env
    else:
        test_url = environ.get("TEST_DATABASE_URL")
        runtime_url = environ.get("DATABASE_URL")
        app_env = environ.get("APP_ENV", "local")
    return validate_postgresql_test_database_url(
        test_database_url=test_url,
        runtime_database_url=runtime_url,
        app_env=app_env,
    )


def build_postgresql_test_settings() -> Settings:
    """Build application settings that explicitly point at the validated test database."""

    test_database_url = _ACTIVE_TEST_DATABASE_URL or get_postgresql_test_database_url()
    return Settings(
        app_env="test",
        database_url=test_database_url,
    )


def activate_postgresql_test_database() -> str:
    """Validate once, then force every Settings() instance in this pytest process to the test DB."""

    global _ACTIVE_TEST_DATABASE_URL

    test_database_url = get_postgresql_test_database_url()
    os.environ["DATABASE_URL"] = test_database_url
    os.environ["APP_ENV"] = "test"
    get_settings.cache_clear()
    _ACTIVE_TEST_DATABASE_URL = test_database_url
    return test_database_url


def postgresql_integration_tests_enabled(
    environ: Mapping[str, str] | None = None,
) -> bool:
    values = os.environ if environ is None else environ
    return values.get("RUN_POSTGRESQL_INTEGRATION_TESTS") == "1"
