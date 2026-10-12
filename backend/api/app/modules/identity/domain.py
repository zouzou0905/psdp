from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class RoleName(StrEnum):
    OPERATIONS = "operations"
    PROCUREMENT = "procurement"
    CREATIVE = "creative"
    ADMIN = "admin"


class ModuleCode(StrEnum):
    OPERATIONS = "operations"
    PROCUREMENT = "procurement"
    CREATIVE = "creative"
    ADMIN = "admin"


class Permission(StrEnum):
    OPERATIONS_DASHBOARD_READ = "operations.dashboard.read"
    SELECTION_READ = "selection.read"
    SELECTION_CREATE = "selection.create"
    SELECTION_EXPORT = "selection.export"
    PROFIT_REVIEW_READ = "profit_review.read"
    FINAL_SELECTION_READ = "final_selection.read"
    FINAL_SELECTION_MANAGE = "final_selection.manage"
    COMPETITOR_REFERENCE_MANAGE = "competitor_reference.manage"
    PROJECT_READ_ASSIGNED = "project.read_assigned"
    LISTING_COPY_READ = "listing_copy.read"
    LISTING_COPY_GENERATE = "listing_copy.generate"
    LISTING_COPY_EDIT = "listing_copy.edit"
    LISTING_COPY_REVIEW = "listing_copy.review"
    LISTING_COPY_HISTORY_READ = "listing_copy.history.read"
    WORKFLOW_READ_ASSIGNED = "workflow.read_assigned"
    AI_FEEDBACK_CREATE_OWN = "ai_feedback.create_own"
    PROCUREMENT_DASHBOARD_READ = "procurement.dashboard.read"
    QUOTE_READ = "quote.read"
    QUOTE_MANAGE = "quote.manage"
    QUOTATION_EXPORT = "quotation.export"
    PURCHASE_REQUEST_READ = "purchase_request.read"
    PURCHASE_REQUEST_MANAGE = "purchase_request.manage"
    FULFILLMENT_READ = "fulfillment.read"
    CREATIVE_DASHBOARD_READ = "creative.dashboard.read"
    CONTENT_TASK_READ_ASSIGNED = "content_task.read_assigned"
    ASSET_READ = "asset.read"
    ASSET_CREATE = "asset.create"
    ASSET_VERSION_CREATE = "asset.version.create"
    GENERATION_REQUEST = "generation.request"
    REVIEW_COMMENT_READ = "review_comment.read"
    ADMIN_DASHBOARD_READ = "admin.dashboard.read"
    USER_MANAGE = "user.manage"
    ROLE_MANAGE = "role.manage"
    ALL_BUSINESS_READ = "all_business.read"
    TASK_READ_ALL = "task.read_all"
    ERROR_READ = "error.read"
    AI_FEEDBACK_READ_ALL = "ai_feedback.read_all"
    AUDIT_LOG_READ = "audit_log.read"
    CAPABILITY_READ = "capability.read"
    SYSTEM_HEALTH_READ = "system_health.read"
    STORE_READ = "store.read"
    STORE_MANAGE = "store.manage"


ROLE_PERMISSIONS: dict[RoleName, frozenset[Permission]] = {
    RoleName.OPERATIONS: frozenset(
        {
            Permission.OPERATIONS_DASHBOARD_READ,
            Permission.SELECTION_READ,
            Permission.SELECTION_CREATE,
            Permission.PROFIT_REVIEW_READ,
            Permission.FINAL_SELECTION_READ,
            Permission.FINAL_SELECTION_MANAGE,
            Permission.COMPETITOR_REFERENCE_MANAGE,
            Permission.PROJECT_READ_ASSIGNED,
            Permission.LISTING_COPY_READ,
            Permission.LISTING_COPY_GENERATE,
            Permission.LISTING_COPY_EDIT,
            Permission.LISTING_COPY_REVIEW,
            Permission.LISTING_COPY_HISTORY_READ,
            Permission.WORKFLOW_READ_ASSIGNED,
            Permission.AI_FEEDBACK_CREATE_OWN,
        }
    ),
    RoleName.PROCUREMENT: frozenset(
        {
            Permission.PROCUREMENT_DASHBOARD_READ,
            Permission.SELECTION_READ,
            Permission.PROFIT_REVIEW_READ,
            Permission.FINAL_SELECTION_READ,
            Permission.QUOTE_READ,
            Permission.QUOTE_MANAGE,
            Permission.PURCHASE_REQUEST_READ,
            Permission.PURCHASE_REQUEST_MANAGE,
            Permission.FULFILLMENT_READ,
            Permission.WORKFLOW_READ_ASSIGNED,
        }
    ),
    RoleName.CREATIVE: frozenset(
        {
            Permission.CREATIVE_DASHBOARD_READ,
            Permission.CONTENT_TASK_READ_ASSIGNED,
            Permission.ASSET_READ,
            Permission.ASSET_CREATE,
            Permission.ASSET_VERSION_CREATE,
            Permission.GENERATION_REQUEST,
            Permission.REVIEW_COMMENT_READ,
            Permission.WORKFLOW_READ_ASSIGNED,
        }
    ),
    RoleName.ADMIN: frozenset(
        permission
        for permission in Permission
        if permission
        not in {
            Permission.SELECTION_EXPORT,
            Permission.QUOTATION_EXPORT,
            Permission.LISTING_COPY_READ,
            Permission.LISTING_COPY_GENERATE,
            Permission.LISTING_COPY_EDIT,
            Permission.LISTING_COPY_REVIEW,
            Permission.LISTING_COPY_HISTORY_READ,
        }
    ),
}


class DataScope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    organization_ids: frozenset[str] = Field(default_factory=frozenset)
    team_ids: frozenset[str] = Field(default_factory=frozenset)
    store_ids: frozenset[str] = Field(default_factory=frozenset)


class UserIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: UUID
    username: str
    display_name: str
    password_hash: str
    is_active: bool
    token_version: int
    authorization_revision: int
    roles: frozenset[RoleName]
    modules: frozenset[ModuleCode]
    direct_permissions: frozenset[Permission]
    permissions: frozenset[Permission]
    scope: DataScope


class Principal(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: UUID
    username: str
    display_name: str
    roles: frozenset[RoleName]
    modules: frozenset[ModuleCode]
    permissions: frozenset[Permission]
    scope: DataScope
    token_version: int
    authorization_revision: int


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=120)
    password: SecretStr


class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.-]+$")
    display_name: str = Field(min_length=1, max_length=160)
    initial_password: SecretStr = Field(min_length=12, max_length=128)


class ViewerResponse(BaseModel):
    user_id: UUID
    username: str
    display_name: str
    roles: list[RoleName]
    modules: list[ModuleCode]
    permissions: list[Permission]
    scope: DataScope
    authorization_revision: int


class AccessContextUser(BaseModel):
    user_id: UUID
    username: str
    display_name: str


class AccessContextResponse(BaseModel):
    user: AccessContextUser
    roles: list[RoleName]
    modules: list[ModuleCode]
    permissions: list[Permission]
    scopes: DataScope
    default_landing: str
    authorization_revision: int


class ModuleListResponse(BaseModel):
    modules: list[ModuleCode]
    default_landing: str


class UserAccessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    username: str
    display_name: str
    is_active: bool
    roles: list[RoleName]
    modules: list[ModuleCode]
    direct_permissions: list[Permission]
    effective_permissions: list[Permission]
    scopes: DataScope
    authorization_revision: int


class UserAccessListResponse(BaseModel):
    items: list[UserAccessResponse]
    total: int = Field(ge=0)


class UpdateRolesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    roles: set[RoleName]
    permissions: set[Permission] = Field(default_factory=set)
    expected_authorization_revision: int = Field(ge=1)


class UpdateModulesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modules: set[ModuleCode]
    expected_authorization_revision: int = Field(ge=1)


class UpdateStoreScopesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    store_ids: set[str]
    expected_authorization_revision: int = Field(ge=1)


MODULE_LANDING_PRIORITY: tuple[ModuleCode, ...] = (
    ModuleCode.ADMIN,
    ModuleCode.OPERATIONS,
    ModuleCode.PROCUREMENT,
    ModuleCode.CREATIVE,
)


def default_landing(modules: frozenset[ModuleCode]) -> str:
    selected = next((module for module in MODULE_LANDING_PRIORITY if module in modules), None)
    return f"/{selected.value}" if selected else "/unauthorized"


def to_access_context(principal: Principal) -> AccessContextResponse:
    return AccessContextResponse(
        user=AccessContextUser(
            user_id=principal.user_id,
            username=principal.username,
            display_name=principal.display_name,
        ),
        roles=sorted(principal.roles),
        modules=sorted(principal.modules),
        permissions=sorted(principal.permissions),
        scopes=principal.scope,
        default_landing=default_landing(principal.modules),
        authorization_revision=principal.authorization_revision,
    )


def to_user_access(user: UserIdentity) -> UserAccessResponse:
    return UserAccessResponse(
        user_id=user.user_id,
        username=user.username,
        display_name=user.display_name,
        is_active=user.is_active,
        roles=sorted(user.roles),
        modules=sorted(user.modules),
        direct_permissions=sorted(user.direct_permissions),
        effective_permissions=sorted(user.permissions),
        scopes=user.scope,
        authorization_revision=user.authorization_revision,
    )


def to_principal(user: UserIdentity) -> Principal:
    return Principal(
        user_id=user.user_id,
        username=user.username,
        display_name=user.display_name,
        roles=user.roles,
        modules=user.modules,
        permissions=user.permissions,
        scope=user.scope,
        token_version=user.token_version,
        authorization_revision=user.authorization_revision,
    )


def to_viewer(principal: Principal) -> ViewerResponse:
    return ViewerResponse(
        user_id=principal.user_id,
        username=principal.username,
        display_name=principal.display_name,
        roles=sorted(principal.roles),
        modules=sorted(principal.modules),
        permissions=sorted(principal.permissions),
        scope=principal.scope,
        authorization_revision=principal.authorization_revision,
    )
