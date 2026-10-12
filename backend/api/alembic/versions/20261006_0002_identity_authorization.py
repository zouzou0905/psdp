"""Add identity, authorization, scoped workspaces, errors, feedback and audit.

Revision ID: 20261006_0002
Revises: 20261006_0001
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261006_0002"
down_revision: str | None = "20261006_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE_PERMISSION_VALUES = {
    "operations": (
        "operations.dashboard.read",
        "selection.read",
        "selection.create",
        "project.read_assigned",
        "listing.read",
        "listing.draft",
        "workflow.read_assigned",
        "ai_feedback.create_own",
    ),
    "procurement": (
        "procurement.dashboard.read",
        "quote.read",
        "quote.manage",
        "purchase_request.read",
        "purchase_request.manage",
        "fulfillment.read",
        "workflow.read_assigned",
    ),
    "creative": (
        "creative.dashboard.read",
        "content_task.read_assigned",
        "asset.read",
        "asset.create",
        "asset.version.create",
        "generation.request",
        "review_comment.read",
        "workflow.read_assigned",
    ),
}
ADMIN_PERMISSION_VALUES = (
    "admin.dashboard.read",
    "user.manage",
    "role.manage",
    "all_business.read",
    "task.read_all",
    "error.read",
    "ai_feedback.read_all",
    "audit_log.read",
    "capability.read",
    "system_health.read",
)
ALL_PERMISSION_VALUES = sorted(set(ADMIN_PERMISSION_VALUES).union(*ROLE_PERMISSION_VALUES.values()))
ROLE_PERMISSION_VALUES["admin"] = tuple(ALL_PERMISSION_VALUES)


def upgrade() -> None:
    op.create_table(
        "iam_users",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(120), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("organization_ids", postgresql.JSONB(), nullable=False),
        sa.Column("team_ids", postgresql.JSONB(), nullable=False),
        sa.Column("store_ids", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_iam_users")),
        sa.UniqueConstraint("username", name=op.f("uq_iam_users_username")),
    )
    op.create_table(
        "iam_roles",
        sa.Column("role_name", sa.String(64), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("role_name", name=op.f("pk_iam_roles")),
    )
    op.create_table(
        "iam_permissions",
        sa.Column("permission_name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("permission_name", name=op.f("pk_iam_permissions")),
    )
    op.create_table(
        "iam_user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_name", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["role_name"], ["iam_roles.role_name"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["iam_users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_name", name=op.f("pk_iam_user_roles")),
    )
    op.create_table(
        "iam_role_permissions",
        sa.Column("role_name", sa.String(64), nullable=False),
        sa.Column("permission_name", sa.String(120), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_name"], ["iam_permissions.permission_name"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["role_name"], ["iam_roles.role_name"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint(
            "role_name", "permission_name", name=op.f("pk_iam_role_permissions")
        ),
    )
    _create_governance_tables()
    _create_workspace_table()
    _seed_role_permissions()


def _create_governance_tables() -> None:
    op.create_table(
        "governance_audit_logs",
        sa.Column("audit_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("actor_roles", postgresql.JSONB(), nullable=False),
        sa.Column("action", sa.String(160), nullable=False),
        sa.Column("resource_type", sa.String(120), nullable=False),
        sa.Column("resource_id", sa.String(160), nullable=True),
        sa.Column("result", sa.String(32), nullable=False),
        sa.Column("trace_id", sa.String(120), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("metadata_summary", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("audit_id", name=op.f("pk_governance_audit_logs")),
    )
    op.create_index(
        op.f("ix_governance_audit_logs_action"),
        "governance_audit_logs",
        ["action"],
    )
    op.create_index(
        op.f("ix_governance_audit_logs_trace_id"),
        "governance_audit_logs",
        ["trace_id"],
    )
    op.create_table(
        "governance_error_records",
        sa.Column("error_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("module", sa.String(80), nullable=False),
        sa.Column("task_id", sa.String(120), nullable=True),
        sa.Column("run_id", sa.String(120), nullable=True),
        sa.Column("action_id", sa.String(120), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trace_id", sa.String(120), nullable=True),
        sa.PrimaryKeyConstraint("error_id", name=op.f("pk_governance_error_records")),
    )
    for column in ("category", "status", "trace_id"):
        op.create_index(
            op.f(f"ix_governance_error_records_{column}"),
            "governance_error_records",
            [column],
        )
    op.create_table(
        "ai_feedback_records",
        sa.Column("feedback_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.String(120), nullable=False),
        sa.Column("run_id", sa.String(120), nullable=False),
        sa.Column("capability_id", sa.String(120), nullable=False),
        sa.Column("capability_release_id", sa.String(120), nullable=False),
        sa.Column("submitted_by", sa.Uuid(), nullable=False),
        sa.Column("feedback_type", sa.String(64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("feedback_id", name=op.f("pk_ai_feedback_records")),
    )
    op.create_index(
        op.f("ix_ai_feedback_records_submitted_by"),
        "ai_feedback_records",
        ["submitted_by"],
    )
    op.create_index(op.f("ix_ai_feedback_records_status"), "ai_feedback_records", ["status"])


def _create_workspace_table() -> None:
    op.create_table(
        "workspace_records",
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("area", sa.String(32), nullable=False),
        sa.Column("record_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("organization_id", sa.String(120), nullable=True),
        sa.Column("team_id", sa.String(120), nullable=True),
        sa.Column("store_id", sa.String(120), nullable=True),
        sa.Column("public_summary", postgresql.JSONB(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("record_id", name=op.f("pk_workspace_records")),
    )
    for column in (
        "area",
        "assignee_id",
        "owner_id",
        "organization_id",
        "team_id",
        "store_id",
    ):
        op.create_index(op.f(f"ix_workspace_records_{column}"), "workspace_records", [column])


def _seed_role_permissions() -> None:
    roles_table = sa.table(
        "iam_roles", sa.column("role_name", sa.String), sa.column("description", sa.String)
    )
    permissions_table = sa.table(
        "iam_permissions",
        sa.column("permission_name", sa.String),
        sa.column("description", sa.String),
    )
    links_table = sa.table(
        "iam_role_permissions",
        sa.column("role_name", sa.String),
        sa.column("permission_name", sa.String),
    )
    op.bulk_insert(
        roles_table,
        [
            {"role_name": role, "description": f"Built-in {role} role"}
            for role in ROLE_PERMISSION_VALUES
        ],
    )
    op.bulk_insert(
        permissions_table,
        [
            {"permission_name": permission, "description": permission}
            for permission in ALL_PERMISSION_VALUES
        ],
    )
    op.bulk_insert(
        links_table,
        [
            {"role_name": role, "permission_name": permission}
            for role, permissions in ROLE_PERMISSION_VALUES.items()
            for permission in permissions
        ],
    )


def downgrade() -> None:
    op.drop_table("workspace_records")
    op.drop_table("ai_feedback_records")
    op.drop_table("governance_error_records")
    op.drop_table("governance_audit_logs")
    op.drop_table("iam_role_permissions")
    op.drop_table("iam_user_roles")
    op.drop_table("iam_permissions")
    op.drop_table("iam_roles")
    op.drop_table("iam_users")
