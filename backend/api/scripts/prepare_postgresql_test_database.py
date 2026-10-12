from __future__ import annotations

import asyncio
import os
from pathlib import Path

from alembic.config import Config

from alembic import command
from app.core.config import get_settings
from app.db.test_database import get_postgresql_test_database_url
from scripts.seed_demo_users import seed


def main() -> None:
    """Upgrade only the explicitly configured and validated PostgreSQL test database."""

    test_database_url = get_postgresql_test_database_url()
    previous_database_url = os.environ.get("DATABASE_URL")
    previous_app_env = os.environ.get("APP_ENV")
    try:
        os.environ["DATABASE_URL"] = test_database_url
        os.environ["APP_ENV"] = "test"
        get_settings.cache_clear()
        api_root = Path(__file__).resolve().parents[1]
        config = Config(str(api_root / "alembic.ini"))
        command.upgrade(config, "head")
        asyncio.run(seed())
    finally:
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url
        if previous_app_env is None:
            os.environ.pop("APP_ENV", None)
        else:
            os.environ["APP_ENV"] = previous_app_env
        get_settings.cache_clear()


if __name__ == "__main__":
    main()
