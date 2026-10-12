from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import create_async_engine

from app.db.base import Base
from app.db.models import WorkspaceRecord
from app.db.session import create_session_factory
from app.modules.identity.domain import RoleName, to_principal
from app.modules.workspace.domain import WorkspaceArea
from app.modules.workspace.repository import (
    SqlAlchemyWorkspaceRepository,
    scoped_workspace_statement,
)
from tests.conftest import RECORD_IDS, USER_IDS, build_users


async def test_database_query_applies_scope_before_loading() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = create_session_factory(engine)
    async with session_factory.begin() as session:
        session.add_all(
            [
                WorkspaceRecord(
                    record_id=RECORD_IDS["operations_allowed"],
                    area="operations",
                    record_type="project",
                    title="allowed",
                    status="pending",
                    assignee_id=USER_IDS[RoleName.OPERATIONS],
                    owner_id=USER_IDS[RoleName.OPERATIONS],
                    organization_id="org_1",
                    team_id="team_operations",
                    store_id="store_operations",
                    public_summary={"data_status": "demo"},
                    updated_at=datetime(2026, 10, 6, tzinfo=UTC),
                ),
                WorkspaceRecord(
                    record_id=RECORD_IDS["operations_denied"],
                    area="operations",
                    record_type="project",
                    title="denied",
                    status="pending",
                    assignee_id=USER_IDS[RoleName.PROCUREMENT],
                    owner_id=USER_IDS[RoleName.PROCUREMENT],
                    organization_id="org_2",
                    team_id="team_other",
                    store_id="store_other",
                    public_summary={"data_status": "demo"},
                    updated_at=datetime(2026, 10, 6, tzinfo=UTC),
                ),
            ]
        )

    operations_user = next(user for user in build_users() if RoleName.OPERATIONS in user.roles)
    principal = to_principal(operations_user)
    statement_text = str(scoped_workspace_statement(principal, WorkspaceArea.OPERATIONS))
    repository = SqlAlchemyWorkspaceRepository(session_factory)
    records = await repository.list_scoped(principal, WorkspaceArea.OPERATIONS)

    assert "workspace_records.store_id IN" in statement_text
    assert [record.response.record_id for record in records] == [RECORD_IDS["operations_allowed"]]
    await engine.dispose()
