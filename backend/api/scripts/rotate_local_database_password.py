"""Rotate the local application role password and atomically update .env."""

import asyncio
import os
import secrets
from pathlib import Path

import asyncpg  # type: ignore[import-untyped]
from sqlalchemy.engine import make_url

DATABASE_URL_KEY = "DATABASE_URL"
EXPECTED_DATABASE_USER = "ai_product_ops_app"
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def read_environment_file(path: Path) -> tuple[list[str], str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    prefix = f"{DATABASE_URL_KEY}="
    value = next((line.removeprefix(prefix) for line in lines if line.startswith(prefix)), None)
    if value is None:
        raise RuntimeError(f"{DATABASE_URL_KEY} is missing from {path}")
    return lines, value


async def rotate() -> None:
    env_path = ENV_PATH
    if not env_path.exists():
        raise RuntimeError(f"{env_path} does not exist")

    lines, database_url = read_environment_file(env_path)
    parsed_url = make_url(database_url)
    if parsed_url.username != EXPECTED_DATABASE_USER or parsed_url.password is None:
        raise RuntimeError("DATABASE_URL does not contain the expected local application role")

    new_password = os.environ.get("NEW_DATABASE_PASSWORD") or secrets.token_urlsafe(32)
    if len(new_password) < 16:
        raise RuntimeError("NEW_DATABASE_PASSWORD must contain at least 16 characters")

    updated_url = parsed_url.set(password=new_password).render_as_string(hide_password=False)
    prefix = f"{DATABASE_URL_KEY}="
    updated_lines = [
        f"{prefix}{updated_url}" if line.startswith(prefix) else line for line in lines
    ]
    pending_path = env_path.with_suffix(".env.pending")
    pending_path.write_text("\n".join((*updated_lines, "")), encoding="utf-8")

    connection: asyncpg.Connection | None = None
    try:
        connection = await asyncpg.connect(
            user=parsed_url.username,
            password=parsed_url.password,
            database=parsed_url.database,
            host=parsed_url.host,
            port=parsed_url.port,
        )
        escaped_password = new_password.replace("'", "''")
        await connection.execute(
            f"ALTER ROLE {EXPECTED_DATABASE_USER} WITH PASSWORD '{escaped_password}'"
        )
        os.replace(pending_path, env_path)
    except Exception:
        pending_path.unlink(missing_ok=True)
        raise
    finally:
        if connection is not None:
            await connection.close()
    print("Rotated the local database password and updated .env; password not displayed.")


if __name__ == "__main__":
    asyncio.run(rotate())
