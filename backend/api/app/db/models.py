from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

JSON_DOCUMENT = JSON().with_variant(JSONB, "postgresql")


class OutboxEvent(Base):
    """Reserved transactional-outbox persistence boundary."""

    __tablename__ = "workflow_outbox_events"

    event_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload: Mapped[dict[str, object]] = mapped_column(JSON_DOCUMENT, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IdempotencyRecord(Base):
    """Reserved idempotency boundary for future write commands."""

    __tablename__ = "workflow_idempotency_records"
    __table_args__ = (
        UniqueConstraint("scope", "idempotency_key", name="uq_workflow_idempotency_scope_key"),
    )

    record_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    scope: Mapped[str] = mapped_column(String(120), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    response_body: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IdentityUser(Base):
    __tablename__ = "iam_users"

    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    authorization_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    organization_ids: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False, default=list)
    team_ids: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class IdentityRole(Base):
    __tablename__ = "iam_roles"

    role_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)


class IdentityPermission(Base):
    __tablename__ = "iam_permissions"

    permission_name: Mapped[str] = mapped_column(String(120), primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)


class IdentityUserRole(Base):
    __tablename__ = "iam_user_roles"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("iam_users.user_id", ondelete="CASCADE"), primary_key=True
    )
    role_name: Mapped[str] = mapped_column(
        String(64), ForeignKey("iam_roles.role_name", ondelete="RESTRICT"), primary_key=True
    )


class IdentityRolePermission(Base):
    __tablename__ = "iam_role_permissions"

    role_name: Mapped[str] = mapped_column(
        String(64), ForeignKey("iam_roles.role_name", ondelete="CASCADE"), primary_key=True
    )
    permission_name: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("iam_permissions.permission_name", ondelete="CASCADE"),
        primary_key=True,
    )


class IdentityModule(Base):
    __tablename__ = "iam_modules"

    module_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)


class IdentityUserModule(Base):
    __tablename__ = "iam_user_modules"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("iam_users.user_id", ondelete="CASCADE"), primary_key=True
    )
    module_code: Mapped[str] = mapped_column(
        String(64), ForeignKey("iam_modules.module_code", ondelete="RESTRICT"), primary_key=True
    )


class IdentityUserPermission(Base):
    __tablename__ = "iam_user_permissions"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("iam_users.user_id", ondelete="CASCADE"), primary_key=True
    )
    permission_name: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("iam_permissions.permission_name", ondelete="RESTRICT"),
        primary_key=True,
    )


class StoreRecord(Base):
    __tablename__ = "stores"

    store_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    marketplace: Mapped[str] = mapped_column(String(80), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    credential_ref: Mapped[str | None] = mapped_column(String(255))
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class IdentityUserStoreScope(Base):
    __tablename__ = "iam_user_store_scopes"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("iam_users.user_id", ondelete="CASCADE"), primary_key=True
    )
    store_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("stores.store_id", ondelete="RESTRICT"), primary_key=True
    )


class GovernanceAuditLog(Base):
    """Append-only audit event. No update/delete repository is exposed."""

    __tablename__ = "governance_audit_logs"

    audit_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    actor_id: Mapped[UUID | None] = mapped_column(Uuid)
    actor_roles: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False, default=list)
    action: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(160))
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(120), index=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    metadata_summary: Mapped[dict[str, str]] = mapped_column(
        JSON_DOCUMENT, nullable=False, default=dict
    )


class GovernanceErrorRecord(Base):
    __tablename__ = "governance_error_records"

    error_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(80), nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(120))
    run_id: Mapped[str | None] = mapped_column(String(120))
    action_id: Mapped[str | None] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, object]] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trace_id: Mapped[str | None] = mapped_column(String(120), index=True)


class AiFeedbackRecord(Base):
    __tablename__ = "ai_feedback_records"

    feedback_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    task_id: Mapped[str] = mapped_column(String(120), nullable=False)
    run_id: Mapped[str] = mapped_column(String(120), nullable=False)
    capability_id: Mapped[str] = mapped_column(String(120), nullable=False)
    capability_release_id: Mapped[str] = mapped_column(String(120), nullable=False)
    submitted_by: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    feedback_type: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class WorkspaceRecord(Base):
    """Minimal scoped read model used by role workspaces until domain tables arrive."""

    __tablename__ = "workspace_records"

    record_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    area: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    record_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    assignee_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    owner_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    organization_id: Mapped[str | None] = mapped_column(String(120), index=True)
    team_id: Mapped[str | None] = mapped_column(String(120), index=True)
    store_id: Mapped[str | None] = mapped_column(String(120), index=True)
    public_summary: Mapped[dict[str, object]] = mapped_column(
        JSON_DOCUMENT, nullable=False, default=dict
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SelectionRecord(Base):
    __tablename__ = "selection_records"

    selection_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    store_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("stores.store_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    marketplace: Mapped[str] = mapped_column(String(80), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(255))
    source_snapshot_ref: Mapped[str | None] = mapped_column(String(255))
    source_version: Mapped[str] = mapped_column(String(80), nullable=False)
    owner_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SelectionQuotationVersion(Base):
    __tablename__ = "selection_quotation_versions"
    __table_args__ = (
        UniqueConstraint("selection_id", "version", name="uq_selection_quotation_version"),
        CheckConstraint(
            "submission_status IN ('draft','submitted')",
            name="ck_selection_quotation_submission_status",
        ),
    )

    quotation_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    selection_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("selection_records.selection_id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    value_status: Mapped[str] = mapped_column(String(24), nullable=False)
    moq: Mapped[int | None] = mapped_column(Integer)
    lead_time_days: Mapped[int | None] = mapped_column(Integer)
    freight_per_unit: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    other_cost_per_unit: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    notes: Mapped[str | None] = mapped_column(Text)
    submission_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="submitted"
    )
    recorded_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SelectionProfitReviewVersion(Base):
    __tablename__ = "selection_profit_review_versions"
    __table_args__ = (
        UniqueConstraint("selection_id", "version", name="uq_selection_profit_review_version"),
    )

    profit_review_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    selection_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("selection_records.selection_id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    quotation_version: Mapped[int] = mapped_column(Integer, nullable=False)
    margin_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    margin_rate: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    currency: Mapped[str | None] = mapped_column(String(3))
    value_status: Mapped[str] = mapped_column(String(24), nullable=False)
    recommendation: Mapped[str] = mapped_column(String(24), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    missing_inputs: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False, default=list)
    task_id: Mapped[str] = mapped_column(String(120), nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SelectionFinalVersion(Base):
    __tablename__ = "selection_final_versions"
    __table_args__ = (
        UniqueConstraint("selection_id", "version", name="uq_selection_final_version"),
    )

    final_selection_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    selection_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("selection_records.selection_id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    profit_review_version: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    decided_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SelectionCompetitorVersion(Base):
    __tablename__ = "selection_competitor_versions"
    __table_args__ = (
        UniqueConstraint(
            "selection_id", "final_version", "position", name="uq_selection_competitor_position"
        ),
    )

    competitor_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    selection_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("selection_records.selection_id", ondelete="CASCADE"), index=True
    )
    final_version: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    bullets: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False)
    recorded_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SelectionAiTask(Base):
    __tablename__ = "selection_ai_tasks"

    task_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    selection_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("selection_records.selection_id", ondelete="CASCADE"), index=True
    )
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    input_version: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(120))
    result_version: Mapped[str | None] = mapped_column(String(120))
    error_code: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SelectionListingDraftVersion(Base):
    __tablename__ = "selection_listing_draft_versions"
    __table_args__ = (
        UniqueConstraint("selection_id", "version", name="uq_selection_listing_draft_version"),
    )

    listing_draft_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    selection_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("selection_records.selection_id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    final_version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    bullets: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    task_id: Mapped[str] = mapped_column(String(120), nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SelectionTableSnapshot(Base):
    """Immutable rows frozen for one stage export."""

    __tablename__ = "selection_table_snapshots"
    __table_args__ = (
        CheckConstraint("row_count >= 0", name="ck_selection_snapshot_row_count"),
    )

    snapshot_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    stage: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(80), nullable=False)
    filters_json: Mapped[dict[str, object]] = mapped_column(
        JSON_DOCUMENT, nullable=False, default=dict
    )
    store_scope_json: Mapped[list[str]] = mapped_column(
        JSON_DOCUMENT, nullable=False, default=list
    )
    requested_by: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SelectionTableSnapshotRow(Base):
    __tablename__ = "selection_table_snapshot_rows"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id", "row_position", name="uq_selection_snapshot_row_position"
        ),
        UniqueConstraint(
            "snapshot_id", "selection_id", name="uq_selection_snapshot_selection"
        ),
        CheckConstraint("row_position > 0", name="ck_selection_snapshot_row_position"),
    )

    snapshot_row_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    snapshot_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("selection_table_snapshots.snapshot_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    row_position: Mapped[int] = mapped_column(Integer, nullable=False)
    selection_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("selection_records.selection_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    selection_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    rendered_row: Mapped[dict[str, object]] = mapped_column(JSON_DOCUMENT, nullable=False)


class SelectionExportJob(Base):
    __tablename__ = "selection_export_jobs"
    __table_args__ = (
        CheckConstraint("row_count >= 0", name="ck_selection_export_row_count"),
        CheckConstraint(
            "status IN ('queued','running','completed','failed')",
            name="ck_selection_export_status",
        ),
    )

    export_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    stage: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    snapshot_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("selection_table_snapshots.snapshot_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    schema_version: Mapped[str] = mapped_column(String(80), nullable=False)
    filters_json: Mapped[dict[str, object]] = mapped_column(
        JSON_DOCUMENT, nullable=False, default=dict
    )
    store_scope_json: Mapped[list[str]] = mapped_column(
        JSON_DOCUMENT, nullable=False, default=list
    )
    requested_by: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    authorization_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(1024))
    file_checksum: Mapped[str | None] = mapped_column(String(64))
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(String(500))
    trace_id: Mapped[str | None] = mapped_column(String(120), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
