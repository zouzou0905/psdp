"""Exercise the live API against database-backed authentication without printing secrets."""

import argparse
import asyncio
from typing import Any, cast

import httpx

from app.core.config import get_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--read-only", action="store_true")
    return parser.parse_args()


async def login(client: httpx.AsyncClient, username: str, password: str) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    response.raise_for_status()
    if response.cookies.get("ai_ops_session") is None:
        raise RuntimeError("Login did not set ai_ops_session")
    set_cookie = response.headers.get("set-cookie", "")
    if "HttpOnly" not in set_cookie or "SameSite=lax" not in set_cookie:
        raise RuntimeError("Session cookie security attributes are incomplete")
    return cast(dict[str, Any], response.json())


async def verify(base_url: str, read_only: bool) -> None:
    settings = get_settings()
    operations_password = settings.demo_operations_password
    admin_password = settings.demo_admin_password
    if operations_password is None or admin_password is None:
        raise RuntimeError("Demo passwords are missing from .env")

    async with (
        httpx.AsyncClient(base_url=base_url) as operations_client,
        httpx.AsyncClient(base_url=base_url) as admin_client,
    ):
        readiness = await operations_client.get("/health/ready")
        readiness.raise_for_status()
        operations_context = await login(
            operations_client,
            "operations_demo",
            operations_password.get_secret_value(),
        )
        if operations_context["roles"] != ["operations"]:
            raise RuntimeError("operations_demo role is not database-derived operations")
        if operations_context["modules"] != ["operations"]:
            raise RuntimeError("operations_demo module is not database-derived operations")
        original_store_ids = operations_context["scopes"]["store_ids"]
        if original_store_ids != ["store_operations_demo"]:
            raise RuntimeError("operations_demo store scope is invalid")

        context_response = await operations_client.get("/api/v1/me/access-context")
        context_response.raise_for_status()
        denied = await operations_client.get("/api/v1/admin/users")
        if denied.status_code != 403:
            raise RuntimeError("operations_demo unexpectedly accessed admin users")

        admin_context = await login(
            admin_client,
            "admin_demo",
            admin_password.get_secret_value(),
        )
        if "admin" not in admin_context["modules"]:
            raise RuntimeError("admin_demo has no admin module")
        users = await admin_client.get("/api/v1/admin/users")
        users.raise_for_status()
        stores = await admin_client.get("/api/v1/admin/stores")
        stores.raise_for_status()

        if not read_only:
            user_id = operations_context["user"]["user_id"]
            user_response = await admin_client.get(f"/api/v1/admin/users/{user_id}")
            user_response.raise_for_status()
            user = user_response.json()
            original_modules = user["modules"]
            original_stores = user["scopes"]["store_ids"]
            revision = user["authorization_revision"]

            revoke = await admin_client.put(
                f"/api/v1/admin/users/{user_id}/modules",
                json={
                    "modules": [],
                    "expected_authorization_revision": revision,
                },
            )
            revoke.raise_for_status()
            revision = revoke.json()["authorization_revision"]
            stale = await operations_client.get("/api/v1/me/access-context")
            if stale.status_code != 401:
                raise RuntimeError("Old session remained valid after module revocation")

            restore_modules = await admin_client.put(
                f"/api/v1/admin/users/{user_id}/modules",
                json={
                    "modules": original_modules,
                    "expected_authorization_revision": revision,
                },
            )
            restore_modules.raise_for_status()
            revision = restore_modules.json()["authorization_revision"]

            alternative_store = next(
                item["store_id"]
                for item in stores.json()["items"]
                if item["store_id"] not in original_stores
            )
            assign_store = await admin_client.put(
                f"/api/v1/admin/users/{user_id}/store-scopes",
                json={
                    "store_ids": [*original_stores, alternative_store],
                    "expected_authorization_revision": revision,
                },
            )
            assign_store.raise_for_status()
            revision = assign_store.json()["authorization_revision"]
            restore_stores = await admin_client.put(
                f"/api/v1/admin/users/{user_id}/store-scopes",
                json={
                    "store_ids": original_stores,
                    "expected_authorization_revision": revision,
                },
            )
            restore_stores.raise_for_status()

        audits = await admin_client.get("/api/v1/admin/audit-logs")
        audits.raise_for_status()
        print(
            {
                "readiness": readiness.status_code,
                "operations_login": 200,
                "operations_admin_access": denied.status_code,
                "admin_users": users.status_code,
                "admin_stores": stores.status_code,
                "authorization_mutation_checked": not read_only,
                "audit_rows": audits.json()["total"],
            }
        )


if __name__ == "__main__":
    arguments = parse_args()
    asyncio.run(verify(arguments.base_url, arguments.read_only))
