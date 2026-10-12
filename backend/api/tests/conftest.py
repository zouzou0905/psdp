from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from app.core.config import Settings
from app.db.test_database import (
    PostgreSQLTestDatabaseSafetyError,
    activate_postgresql_test_database,
    postgresql_integration_tests_enabled,
)
from app.main import create_app
from app.modules.admin.domain import (
    AiFeedback,
    ErrorCategory,
    ErrorRecord,
    FeedbackStatus,
    RecordStatus,
    Severity,
)
from app.modules.admin.repository import InMemoryAdminRepository
from app.modules.audit.repository import InMemoryAuditRepository
from app.modules.identity.domain import (
    ROLE_PERMISSIONS,
    DataScope,
    ModuleCode,
    RoleName,
    UserIdentity,
)
from app.modules.identity.repository import InMemoryIdentityRepository
from app.modules.identity.security import PasswordService
from app.modules.store.domain import Store, StoreStatus
from app.modules.store.repository import InMemoryStoreRepository
from app.modules.workspace.domain import (
    ScopedWorkspaceRecord,
    WorkspaceArea,
    WorkspaceRecordResponse,
)
from app.modules.workspace.repository import InMemoryWorkspaceRepository

PASSWORD = "valid-test-password"
USER_IDS = {
    RoleName.OPERATIONS: UUID("10000000-0000-0000-0000-000000000001"),
    RoleName.PROCUREMENT: UUID("20000000-0000-0000-0000-000000000002"),
    RoleName.CREATIVE: UUID("30000000-0000-0000-0000-000000000003"),
    RoleName.ADMIN: UUID("40000000-0000-0000-0000-000000000004"),
}
RECORD_IDS = {
    "operations_allowed": UUID("a0000000-0000-0000-0000-000000000001"),
    "operations_denied": UUID("a0000000-0000-0000-0000-000000000002"),
    "procurement_allowed": UUID("b0000000-0000-0000-0000-000000000001"),
    "procurement_denied": UUID("b0000000-0000-0000-0000-000000000002"),
    "creative_allowed": UUID("c0000000-0000-0000-0000-000000000001"),
    "creative_denied": UUID("c0000000-0000-0000-0000-000000000002"),
}


def pytest_configure() -> None:
    """Reject an unsafe PostgreSQL target before test collection or fixture writes."""

    if postgresql_integration_tests_enabled():
        try:
            activate_postgresql_test_database()
        except PostgreSQLTestDatabaseSafetyError as exc:
            raise pytest.UsageError(str(exc)) from None


class ConfigurableDatabaseProbe:
    def __init__(self, ready: bool = True) -> None:
        self.ready = ready

    async def is_ready(self) -> bool:
        return self.ready


def build_users() -> list[UserIdentity]:
    password_hash = PasswordService().hash(PASSWORD)
    return [
        UserIdentity(
            user_id=USER_IDS[role],
            username=f"{role.value}_demo",
            display_name=f"{role.value.title()} Demo",
            password_hash=password_hash,
            is_active=True,
            token_version=1,
            authorization_revision=1,
            roles=frozenset({role}),
            modules=(
                frozenset(ModuleCode)
                if role is RoleName.ADMIN
                else frozenset({ModuleCode(role.value)})
            ),
            direct_permissions=frozenset(),
            permissions=ROLE_PERMISSIONS[role],
            scope=DataScope(
                organization_ids=frozenset({"org_1"}),
                team_ids=frozenset({f"team_{role.value}"}),
                store_ids=frozenset({f"store_{role.value}"}),
            ),
        )
        for role in RoleName
    ]


def _record(
    key: str,
    area: WorkspaceArea,
    *,
    assignee: UUID,
    organization_id: str,
    team_id: str,
    store_id: str,
) -> ScopedWorkspaceRecord:
    return ScopedWorkspaceRecord(
        response=WorkspaceRecordResponse(
            record_id=RECORD_IDS[key],
            record_type={
                WorkspaceArea.OPERATIONS: "project",
                WorkspaceArea.PROCUREMENT: "purchase_request",
                WorkspaceArea.CREATIVE: "content_task",
            }[area],
            title=f"DEMO {key}",
            status="pending",
            store_id=store_id,
            updated_at=datetime(2026, 10, 6, tzinfo=UTC),
            summary={"data_status": "demo"},
        ),
        area=area,
        assignee_id=assignee,
        owner_id=assignee,
        scope=DataScope(
            organization_ids=frozenset({organization_id}),
            team_ids=frozenset({team_id}),
            store_ids=frozenset({store_id}),
        ),
    )


def build_workspace_records() -> list[ScopedWorkspaceRecord]:
    return [
        _record(
            "operations_allowed",
            WorkspaceArea.OPERATIONS,
            assignee=USER_IDS[RoleName.OPERATIONS],
            organization_id="org_1",
            team_id="team_operations",
            store_id="store_operations",
        ),
        _record(
            "operations_denied",
            WorkspaceArea.OPERATIONS,
            assignee=UUID("90000000-0000-0000-0000-000000000001"),
            organization_id="org_2",
            team_id="team_other",
            store_id="store_other",
        ),
        _record(
            "procurement_allowed",
            WorkspaceArea.PROCUREMENT,
            assignee=USER_IDS[RoleName.PROCUREMENT],
            organization_id="org_1",
            team_id="team_procurement",
            store_id="store_procurement",
        ),
        _record(
            "procurement_denied",
            WorkspaceArea.PROCUREMENT,
            assignee=UUID("90000000-0000-0000-0000-000000000002"),
            organization_id="org_2",
            team_id="team_other",
            store_id="store_other",
        ),
        _record(
            "creative_allowed",
            WorkspaceArea.CREATIVE,
            assignee=USER_IDS[RoleName.CREATIVE],
            organization_id="org_1",
            team_id="team_creative",
            store_id="store_creative",
        ),
        _record(
            "creative_denied",
            WorkspaceArea.CREATIVE,
            assignee=UUID("90000000-0000-0000-0000-000000000003"),
            organization_id="org_2",
            team_id="team_other",
            store_id="store_other",
        ),
    ]


@pytest.fixture
def database_probe() -> ConfigurableDatabaseProbe:
    return ConfigurableDatabaseProbe()


@pytest.fixture
def audit_repository() -> InMemoryAuditRepository:
    return InMemoryAuditRepository()


@pytest.fixture
def workspace_repository() -> InMemoryWorkspaceRepository:
    return InMemoryWorkspaceRepository(build_workspace_records())


@pytest.fixture
def identity_repository() -> InMemoryIdentityRepository:
    return InMemoryIdentityRepository(build_users())


@pytest.fixture
def store_repository() -> InMemoryStoreRepository:
    now = datetime(2026, 10, 6, tzinfo=UTC)
    return InMemoryStoreRepository(
        [
            Store(
                store_id=store_id,
                display_name=f"DEMO {store_id}",
                marketplace="demo",
                organization_id="org_1" if store_id != "store_other" else "org_2",
                status=StoreStatus.ACTIVE,
                credential_ref=None,
                revision=1,
                created_at=now,
                updated_at=now,
            )
            for store_id in (
                "store_operations",
                "store_procurement",
                "store_creative",
                "store_other",
            )
        ]
    )


@pytest.fixture
def admin_repository() -> InMemoryAdminRepository:
    return InMemoryAdminRepository(
        errors=[
            ErrorRecord(
                error_id=UUID("e0000000-0000-0000-0000-000000000001"),
                category=ErrorCategory.INTEGRATION,
                severity=Severity.ERROR,
                status=RecordStatus.OPEN,
                module="integration",
                task_id="tsk_demo",
                run_id="run_demo",
                action_id="act_demo",
                summary=(
                    "database postgresql://user:password@db/app Authorization Bearer secret-token"
                ),
                occurred_at=datetime(2026, 10, 6, tzinfo=UTC),
                resolved_at=None,
                trace_id="trace_demo",
            )
        ],
        feedback=[
            AiFeedback(
                feedback_id=UUID("f0000000-0000-0000-0000-000000000001"),
                task_id="tsk_demo",
                run_id="run_demo",
                capability_id="listing-copy",
                capability_release_id="rel_demo",
                submitted_by=USER_IDS[RoleName.OPERATIONS],
                feedback_type="correction",
                summary="DEMO feedback without full prompt",
                status=FeedbackStatus.NEW,
                created_at=datetime(2026, 10, 6, tzinfo=UTC),
            )
        ],
    )


@pytest.fixture
def app(
    database_probe: ConfigurableDatabaseProbe,
    audit_repository: InMemoryAuditRepository,
    workspace_repository: InMemoryWorkspaceRepository,
    admin_repository: InMemoryAdminRepository,
    identity_repository: InMemoryIdentityRepository,
    store_repository: InMemoryStoreRepository,
) -> FastAPI:
    settings = Settings(
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        cors_origins=["http://test.local"],
        auth_secret_key=SecretStr("test-secret-with-sufficient-random-looking-length"),
    )
    return create_app(
        settings,
        database_probe=database_probe,
        identity_repository=identity_repository,
        store_repository=store_repository,
        audit_repository=audit_repository,
        admin_repository=admin_repository,
        workspace_repository=workspace_repository,
    )


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest.fixture
async def auth_headers(client: httpx.AsyncClient) -> dict[RoleName, dict[str, str]]:
    headers: dict[RoleName, dict[str, str]] = {}
    for role in RoleName:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": f"{role.value}_demo", "password": PASSWORD},
        )
        assert response.status_code == 200
        session_cookie = response.cookies.get("ai_ops_session")
        assert session_cookie is not None
        headers[role] = {"Cookie": f"ai_ops_session={session_cookie}"}
    return headers
