import pytest

import app.db.test_database as test_database
from app.core.config import Settings
from app.db.test_database import (
    PostgreSQLTestDatabaseSafetyError,
    get_postgresql_test_database_url,
    validate_postgresql_test_database_url,
)

DEV_URL = "postgresql+asyncpg://app:dev-secret@127.0.0.1:5432/ai_product_ops_dev"
TEST_URL = "postgresql+asyncpg://app:test-secret@127.0.0.1:5432/ai_product_ops_test"


def test_accepts_dedicated_test_database() -> None:
    assert (
        validate_postgresql_test_database_url(
            test_database_url=TEST_URL,
            runtime_database_url=DEV_URL,
            app_env="local",
        )
        == TEST_URL
    )


def test_activation_forces_all_runtime_settings_to_test_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(test_database, "_ACTIVE_TEST_DATABASE_URL", None)
    monkeypatch.setenv("DATABASE_URL", DEV_URL)
    monkeypatch.setenv("TEST_DATABASE_URL", TEST_URL)
    monkeypatch.setenv("APP_ENV", "local")

    assert test_database.activate_postgresql_test_database() == TEST_URL
    assert Settings().database_url == TEST_URL
    assert Settings().app_env == "test"


def test_missing_test_url_never_falls_back_to_runtime_database() -> None:
    with pytest.raises(PostgreSQLTestDatabaseSafetyError, match="TEST_DATABASE_URL is required"):
        get_postgresql_test_database_url(
            {
                "RUN_POSTGRESQL_INTEGRATION_TESTS": "1",
                "DATABASE_URL": DEV_URL,
                "APP_ENV": "local",
            }
        )


@pytest.mark.parametrize(
    "database_name",
    ["ai_product_ops_dev", "postgres", "template0", "template1"],
)
def test_rejects_forbidden_database_names(database_name: str) -> None:
    with pytest.raises(PostgreSQLTestDatabaseSafetyError):
        validate_postgresql_test_database_url(
            test_database_url=(
                f"postgresql+asyncpg://app:test-secret@127.0.0.1:5432/{database_name}"
            ),
            runtime_database_url=DEV_URL,
            app_env="local",
        )


def test_rejects_database_without_test_suffix() -> None:
    with pytest.raises(PostgreSQLTestDatabaseSafetyError, match="must end in '_test'"):
        validate_postgresql_test_database_url(
            test_database_url="postgresql+asyncpg://app:secret@db.local:5432/scratch",
            runtime_database_url=DEV_URL,
            app_env="local",
        )


def test_rejects_same_database_with_localhost_alias() -> None:
    with pytest.raises(PostgreSQLTestDatabaseSafetyError, match="same database"):
        validate_postgresql_test_database_url(
            test_database_url=(
                "postgresql+asyncpg://other:test-secret@localhost:5432/shared_test"
            ),
            runtime_database_url=(
                "postgresql+asyncpg://app:runtime-secret@127.0.0.1:5432/shared_test"
            ),
            app_env="local",
        )


@pytest.mark.parametrize("app_env", ["staging", "production"])
def test_rejects_non_test_runtime_environments(app_env: str) -> None:
    with pytest.raises(PostgreSQLTestDatabaseSafetyError, match="APP_ENV"):
        validate_postgresql_test_database_url(
            test_database_url=TEST_URL,
            runtime_database_url=DEV_URL,
            app_env=app_env,
        )


@pytest.mark.parametrize("database_name", ["orders_prod_test", "orders_staging_test"])
def test_rejects_production_or_staging_database_names(database_name: str) -> None:
    with pytest.raises(PostgreSQLTestDatabaseSafetyError, match="staging or production"):
        validate_postgresql_test_database_url(
            test_database_url=(
                f"postgresql+asyncpg://app:test-secret@db.local:5432/{database_name}"
            ),
            runtime_database_url=DEV_URL,
            app_env="local",
        )


def test_safety_error_does_not_expose_credentials_or_full_url() -> None:
    secret = "never-print-this-password"
    unsafe_url = (
        f"postgresql+asyncpg://sensitive-user:{secret}@127.0.0.1:5432/ai_product_ops_dev"
    )
    with pytest.raises(PostgreSQLTestDatabaseSafetyError) as exc_info:
        validate_postgresql_test_database_url(
            test_database_url=unsafe_url,
            runtime_database_url=DEV_URL,
            app_env="local",
        )
    message = str(exc_info.value)
    assert secret not in message
    assert "sensitive-user" not in message
    assert unsafe_url not in message
