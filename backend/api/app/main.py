from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from secrets import token_urlsafe

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_v1_router
from app.core.config import Settings, get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.db.health import DatabaseHealthProbe, SqlAlchemyDatabaseHealthProbe
from app.db.session import create_engine, create_session_factory
from app.integrations.deepseek import DeepSeekProvider
from app.integrations.gateway import RoutedCapabilityGateway
from app.modules.admin.redaction import RedactionService
from app.modules.admin.repository import (
    AdminRepository,
    SqlAlchemyAdminRepository,
)
from app.modules.admin.service import AdminQueryService
from app.modules.audit.repository import AuditRepository, SqlAlchemyAuditRepository
from app.modules.audit.service import AuditService
from app.modules.capability.service import CapabilityStatusService
from app.modules.dashboard.service import DashboardService
from app.modules.health.router import router as health_router
from app.modules.health.service import HealthService
from app.modules.identity.admin_service import IdentityAdminService
from app.modules.identity.repository import IdentityRepository, SqlAlchemyIdentityRepository
from app.modules.identity.security import PasswordService, TokenService
from app.modules.identity.service import AuthenticationService
from app.modules.selection.repository import SqlAlchemySelectionRepository
from app.modules.selection.service import SelectionService
from app.modules.selection_export.domain import SelectionExportStage
from app.modules.selection_export.exporter import (
    InitialSelectionExporter,
    QuotationExporter,
    StageExporter,
)
from app.modules.selection_export.repository import (
    SelectionExportRepository,
    SqlAlchemySelectionExportRepository,
)
from app.modules.selection_export.service import SelectionExportService
from app.modules.selection_skill.registry import SkillRegistry
from app.modules.selection_skill.service import SelectionSkillService
from app.modules.store.repository import SqlAlchemyStoreRepository, StoreRepository
from app.modules.store.service import StoreService
from app.modules.workspace.repository import (
    SqlAlchemyWorkspaceRepository,
    WorkspaceRepository,
)
from app.modules.workspace.service import WorkspaceService


def create_app(
    settings: Settings | None = None,
    *,
    database_probe: DatabaseHealthProbe | None = None,
    identity_repository: IdentityRepository | None = None,
    audit_repository: AuditRepository | None = None,
    admin_repository: AdminRepository | None = None,
    workspace_repository: WorkspaceRepository | None = None,
    store_repository: StoreRepository | None = None,
    deepseek_provider: DeepSeekProvider | None = None,
    selection_export_repository: SelectionExportRepository | None = None,
    initial_selection_exporter: StageExporter | None = None,
    quotation_exporter: StageExporter | None = None,
) -> FastAPI:
    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)
    engine = create_engine(runtime_settings)
    session_factory = create_session_factory(engine)
    if runtime_settings.auth_secret_key is None:
        if runtime_settings.app_env in {"staging", "production"}:
            raise RuntimeError("AUTH_SECRET_KEY is required in staging and production")
        auth_secret = token_urlsafe(48)
    else:
        auth_secret = runtime_settings.auth_secret_key.get_secret_value()

    resolved_audit_repository = audit_repository or SqlAlchemyAuditRepository(session_factory)
    resolved_identity_repository = identity_repository or SqlAlchemyIdentityRepository(
        session_factory
    )
    resolved_admin_repository = admin_repository or SqlAlchemyAdminRepository(session_factory)
    resolved_workspace_repository = workspace_repository or SqlAlchemyWorkspaceRepository(
        session_factory
    )
    resolved_store_repository = store_repository or SqlAlchemyStoreRepository(session_factory)
    audit_service = AuditService(resolved_audit_repository)
    resolved_deepseek_provider = deepseek_provider or DeepSeekProvider(
        api_key=runtime_settings.deepseek_api_key,
        base_url=runtime_settings.deepseek_base_url,
        model=runtime_settings.deepseek_model,
        connect_timeout_seconds=runtime_settings.deepseek_connect_timeout_seconds,
        request_timeout_seconds=runtime_settings.deepseek_request_timeout_seconds,
        max_retries=runtime_settings.deepseek_max_retries,
    )
    capability_gateway = RoutedCapabilityGateway(
        {DeepSeekProvider.capability_id: resolved_deepseek_provider}
    )
    password_service = PasswordService()
    authentication_service = AuthenticationService(
        resolved_identity_repository,
        password_service,
        TokenService(
            auth_secret,
            runtime_settings.auth_issuer,
            runtime_settings.auth_audience,
            runtime_settings.auth_session_ttl_minutes,
        ),
        audit_service,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        await engine.dispose()

    application = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        description=(
            "Governed backend for the AI product operations platform. "
            "Demo responses are not authoritative operating facts."
        ),
        lifespan=lifespan,
    )
    application.state.settings = runtime_settings
    application.state.engine = engine
    application.state.session_factory = session_factory
    application.state.audit_service = audit_service
    application.state.capability_gateway = capability_gateway
    application.state.deepseek_provider = resolved_deepseek_provider
    application.state.capability_status_service = CapabilityStatusService(
        resolved_deepseek_provider, audit_service
    )
    application.state.authentication_service = authentication_service
    application.state.identity_admin_service = IdentityAdminService(
        resolved_identity_repository,
        resolved_store_repository,
        audit_service,
        password_service,
    )
    application.state.store_service = StoreService(resolved_store_repository, audit_service)
    admin_query_service = AdminQueryService(
        resolved_admin_repository, audit_service, RedactionService()
    )
    application.state.admin_query_service = admin_query_service
    application.state.error_recorder = admin_query_service
    application.state.workspace_service = WorkspaceService(
        resolved_workspace_repository, audit_service
    )
    application.state.health_service = HealthService(
        database_probe or SqlAlchemyDatabaseHealthProbe(engine)
    )
    application.state.dashboard_service = DashboardService(resolved_workspace_repository)
    application.state.selection_service = SelectionService(
        SqlAlchemySelectionRepository(session_factory), audit_service
    )
    application.state.selection_skill_service = SelectionSkillService(
        SkillRegistry(runtime_settings.selection_skill_assets_path), audit_service
    )
    application.state.selection_export_service = SelectionExportService(
        selection_export_repository
        or SqlAlchemySelectionExportRepository(session_factory),
        audit_service,
        {
            SelectionExportStage.INITIAL_SELECTION: initial_selection_exporter
            or InitialSelectionExporter(),
            SelectionExportStage.QUOTATION: quotation_exporter or QuotationExporter(),
        },
        runtime_settings.export_storage_path,
        runtime_settings.export_file_ttl_hours,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestContextMiddleware)
    install_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(api_v1_router, prefix=runtime_settings.api_v1_prefix)
    return application


app = create_app()
