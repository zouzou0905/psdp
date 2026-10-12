import asyncio
import json

from sqlalchemy import inspect, select

from app.core.config import get_settings
from app.db.models import GovernanceAuditLog, IdentityUser, StoreRecord
from app.db.session import create_engine, create_session_factory
from app.modules.identity.repository import SqlAlchemyIdentityRepository

REQUIRED_TABLES = {
    "iam_users",
    "iam_roles",
    "iam_permissions",
    "iam_user_roles",
    "iam_user_modules",
    "iam_user_store_scopes",
    "stores",
    "governance_audit_logs",
}
DEMO_USERS = (
    "operations_demo",
    "procurement_demo",
    "creative_demo",
    "admin_demo",
)


async def verify() -> None:
    settings = get_settings()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    try:
        async with engine.connect() as connection:
            table_names = set(
                await connection.run_sync(
                    lambda sync_connection: inspect(sync_connection).get_table_names()
                )
            )
        missing = sorted(REQUIRED_TABLES.difference(table_names))
        if missing:
            raise RuntimeError(f"Missing required tables: {', '.join(missing)}")

        async with session_factory() as session:
            user_count = len(
                (
                    await session.scalars(
                        select(IdentityUser).where(IdentityUser.username.in_(DEMO_USERS))
                    )
                ).all()
            )
            store_count = len((await session.scalars(select(StoreRecord))).all())
            audit_count = len((await session.scalars(select(GovernanceAuditLog))).all())

        repository = SqlAlchemyIdentityRepository(session_factory)
        operations = await repository.get_by_username("operations_demo")
        if operations is None:
            raise RuntimeError("operations_demo is missing")
        if {role.value for role in operations.roles} != {"operations"}:
            raise RuntimeError("operations_demo role assignment is invalid")
        if {module.value for module in operations.modules} != {"operations"}:
            raise RuntimeError("operations_demo module assignment is invalid")
        if not operations.scope.store_ids:
            raise RuntimeError("operations_demo has no store scope")

        print(
            json.dumps(
                {
                    "database": "ready",
                    "required_tables": len(REQUIRED_TABLES),
                    "demo_users": user_count,
                    "stores": store_count,
                    "audit_rows": audit_count,
                    "operations_modules": sorted(operations.modules),
                    "operations_store_ids": sorted(operations.scope.store_ids),
                },
                ensure_ascii=False,
            )
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify())
