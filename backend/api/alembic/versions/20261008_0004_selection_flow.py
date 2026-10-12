"""Add the linked selection, quotation, review and final-selection flow.

Revision ID: 20261008_0004
Revises: 20261007_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261008_0004"
down_revision: str | None = "20261007_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_PERMISSIONS = (
    "profit_review.read",
    "final_selection.read",
    "final_selection.manage",
    "competitor_reference.manage",
)


def upgrade() -> None:
    op.create_table(
        "selection_records",
        sa.Column("selection_id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.String(64), nullable=False),
        sa.Column("marketplace", sa.String(80), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_ref", sa.String(255)),
        sa.Column("source_snapshot_ref", sa.String(255)),
        sa.Column("source_version", sa.String(80), nullable=False),
        sa.Column("owner_id", sa.Uuid()),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("revision", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["store_id"], ["stores.store_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("selection_id"),
    )
    op.create_index("ix_selection_records_store_id", "selection_records", ["store_id"])
    op.create_index("ix_selection_records_owner_id", "selection_records", ["owner_id"])
    op.create_index("ix_selection_records_stage", "selection_records", ["stage"])

    _create_quotation_table()
    _create_profit_table()
    _create_final_and_competitor_tables()
    _create_ai_tables()
    _seed_permissions()


def _create_quotation_table() -> None:
    op.create_table(
        "selection_quotation_versions",
        sa.Column("quotation_id", sa.Uuid(), nullable=False),
        sa.Column("selection_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("supplier_name", sa.String(255), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4)),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("value_status", sa.String(24), nullable=False),
        sa.Column("moq", sa.Integer()),
        sa.Column("lead_time_days", sa.Integer()),
        sa.Column("freight_per_unit", sa.Numeric(18, 4)),
        sa.Column("other_cost_per_unit", sa.Numeric(18, 4)),
        sa.Column("target_price", sa.Numeric(18, 4)),
        sa.Column("notes", sa.Text()),
        sa.Column("recorded_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["selection_id"], ["selection_records.selection_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("quotation_id"),
        sa.UniqueConstraint("selection_id", "version", name="uq_selection_quotation_version"),
    )
    op.create_index(
        "ix_selection_quotation_versions_selection_id",
        "selection_quotation_versions",
        ["selection_id"],
    )


def _create_profit_table() -> None:
    op.create_table(
        "selection_profit_review_versions",
        sa.Column("profit_review_id", sa.Uuid(), nullable=False),
        sa.Column("selection_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("quotation_version", sa.Integer(), nullable=False),
        sa.Column("margin_amount", sa.Numeric(18, 4)),
        sa.Column("margin_rate", sa.Numeric(9, 6)),
        sa.Column("currency", sa.String(3)),
        sa.Column("value_status", sa.String(24), nullable=False),
        sa.Column("recommendation", sa.String(24), nullable=False),
        sa.Column("explanation", sa.Text()),
        sa.Column(
            "missing_inputs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("task_id", sa.String(120), nullable=False),
        sa.Column("run_id", sa.String(120)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["selection_id"], ["selection_records.selection_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("profit_review_id"),
        sa.UniqueConstraint("selection_id", "version", name="uq_selection_profit_review_version"),
    )
    op.create_index(
        "ix_selection_profit_review_versions_selection_id",
        "selection_profit_review_versions",
        ["selection_id"],
    )


def _create_final_and_competitor_tables() -> None:
    op.create_table(
        "selection_final_versions",
        sa.Column("final_selection_id", sa.Uuid(), nullable=False),
        sa.Column("selection_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("profit_review_version", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("decided_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["selection_id"], ["selection_records.selection_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("final_selection_id"),
        sa.UniqueConstraint("selection_id", "version", name="uq_selection_final_version"),
    )
    op.create_index(
        "ix_selection_final_versions_selection_id",
        "selection_final_versions",
        ["selection_id"],
    )
    op.create_table(
        "selection_competitor_versions",
        sa.Column("competitor_id", sa.Uuid(), nullable=False),
        sa.Column("selection_id", sa.Uuid(), nullable=False),
        sa.Column("final_version", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("bullets", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recorded_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["selection_id"], ["selection_records.selection_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("competitor_id"),
        sa.UniqueConstraint(
            "selection_id", "final_version", "position", name="uq_selection_competitor_position"
        ),
    )
    op.create_index(
        "ix_selection_competitor_versions_selection_id",
        "selection_competitor_versions",
        ["selection_id"],
    )


def _create_ai_tables() -> None:
    op.create_table(
        "selection_ai_tasks",
        sa.Column("task_id", sa.String(120), nullable=False),
        sa.Column("selection_id", sa.Uuid(), nullable=False),
        sa.Column("task_type", sa.String(32), nullable=False),
        sa.Column("input_version", sa.String(120), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("run_id", sa.String(120)),
        sa.Column("result_version", sa.String(120)),
        sa.Column("error_code", sa.String(80)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["selection_id"], ["selection_records.selection_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("task_id"),
    )
    op.create_index("ix_selection_ai_tasks_selection_id", "selection_ai_tasks", ["selection_id"])
    op.create_table(
        "selection_listing_draft_versions",
        sa.Column("listing_draft_id", sa.Uuid(), nullable=False),
        sa.Column("selection_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("final_version", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("bullets", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("task_id", sa.String(120), nullable=False),
        sa.Column("run_id", sa.String(120)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["selection_id"], ["selection_records.selection_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("listing_draft_id"),
        sa.UniqueConstraint(
            "selection_id", "version", name="uq_selection_listing_draft_version"
        ),
    )
    op.create_index(
        "ix_selection_listing_draft_versions_selection_id",
        "selection_listing_draft_versions",
        ["selection_id"],
    )


def _seed_permissions() -> None:
    permissions = sa.table(
        "iam_permissions",
        sa.column("permission_name", sa.String),
        sa.column("description", sa.String),
    )
    role_permissions = sa.table(
        "iam_role_permissions",
        sa.column("role_name", sa.String),
        sa.column("permission_name", sa.String),
    )
    op.bulk_insert(
        permissions,
        [{"permission_name": item, "description": item} for item in NEW_PERMISSIONS],
    )
    op.bulk_insert(
        role_permissions,
        [
            {"role_name": "procurement", "permission_name": permission}
            for permission in ("selection.read", "profit_review.read", "final_selection.read")
        ]
        + [
            {"role_name": "operations", "permission_name": permission}
            for permission in (
                "profit_review.read",
                "final_selection.read",
                "final_selection.manage",
                "competitor_reference.manage",
            )
        ]
        + [
            {"role_name": "admin", "permission_name": permission}
            for permission in NEW_PERMISSIONS
        ],
    )


def downgrade() -> None:
    op.drop_table("selection_listing_draft_versions")
    op.drop_table("selection_ai_tasks")
    op.drop_table("selection_competitor_versions")
    op.drop_table("selection_final_versions")
    op.drop_table("selection_profit_review_versions")
    op.drop_table("selection_quotation_versions")
    op.drop_table("selection_records")
    op.execute(
        "DELETE FROM iam_role_permissions WHERE permission_name IN "
        "('profit_review.read','final_selection.read','final_selection.manage',"
        "'competitor_reference.manage')"
    )
    op.execute(
        "DELETE FROM iam_permissions WHERE permission_name IN "
        "('profit_review.read','final_selection.read','final_selection.manage',"
        "'competitor_reference.manage')"
    )
