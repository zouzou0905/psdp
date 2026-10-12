"""Create a local .env and rotate the temporary PostgreSQL application password.

This script is intentionally local-only. It never prints generated credentials.
"""

import argparse
import asyncio
import os
import secrets
from pathlib import Path
from urllib.parse import quote

import asyncpg  # type: ignore[import-untyped]

DATABASE_HOST = "127.0.0.1"
DATABASE_PORT = 5432
DATABASE_NAME = "ai_product_ops_dev"
DATABASE_USER = "ai_product_ops_app"
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Replace an existing local .env")
    return parser.parse_args()


async def configure(force: bool) -> None:
    current_password = os.environ.get("CURRENT_DATABASE_PASSWORD")
    if not current_password:
        raise RuntimeError("CURRENT_DATABASE_PASSWORD is required for the one-time rotation")

    env_path = ENV_PATH
    temporary_path = env_path.with_suffix(".env.pending")
    if env_path.exists() and not force:
        raise RuntimeError(
            f"{env_path} already exists; use --force only when replacement is intended"
        )

    database_password = secrets.token_urlsafe(32)
    auth_secret = secrets.token_urlsafe(48)
    demo_passwords = {
        role: secrets.token_urlsafe(18)
        for role in (
            "OPERATIONS",
            "PROCUREMENT",
            "CREATIVE",
            "ADMIN",
        )
    }
    encoded_password = quote(database_password, safe="")
    contents = "\n".join(
        (
            "APP_NAME=AI Product Operations Platform API",
            "APP_ENV=local",
            "APP_VERSION=0.1.0",
            "API_V1_PREFIX=/api/v1",
            (
                "DATABASE_URL=postgresql+asyncpg://"
                f"{DATABASE_USER}:{encoded_password}@{DATABASE_HOST}:{DATABASE_PORT}/"
                f"{DATABASE_NAME}"
            ),
            "DATABASE_ECHO=false",
            "DATABASE_POOL_SIZE=5",
            "DATABASE_MAX_OVERFLOW=10",
            "DATABASE_CONNECT_TIMEOUT_SECONDS=5",
            'CORS_ORIGINS=["http://localhost:3001","http://127.0.0.1:3001"]',
            "LOG_LEVEL=INFO",
            f"AUTH_SECRET_KEY={auth_secret}",
            "AUTH_SESSION_TTL_MINUTES=30",
            "AUTH_ISSUER=ai-product-operations-platform",
            "AUTH_AUDIENCE=ai-product-operations-api",
            "AUTH_COOKIE_SAMESITE=lax",
            *(f"DEMO_{role}_PASSWORD={password}" for role, password in demo_passwords.items()),
            "REDIS_URL=redis://localhost:6379/0",
            "CELERY_BROKER_URL=redis://localhost:6379/1",
            "CELERY_RESULT_BACKEND=redis://localhost:6379/2",
            "",
        )
    )
    temporary_path.write_text(contents, encoding="utf-8")

    connection: asyncpg.Connection | None = None
    try:
        connection = await asyncpg.connect(
            user=DATABASE_USER,
            password=current_password,
            database=DATABASE_NAME,
            host=DATABASE_HOST,
            port=DATABASE_PORT,
        )
        escaped_password = database_password.replace("'", "''")
        await connection.execute(f"ALTER ROLE {DATABASE_USER} WITH PASSWORD '{escaped_password}'")
        os.replace(temporary_path, env_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    finally:
        if connection is not None:
            await connection.close()

    print(f"Created {env_path} and rotated the local application database password.")
    print("Generated four demo passwords in .env; no credentials were printed.")


if __name__ == "__main__":
    arguments = parse_args()
    asyncio.run(configure(arguments.force))
