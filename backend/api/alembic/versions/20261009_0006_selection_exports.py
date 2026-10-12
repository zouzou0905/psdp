"""Add immutable selection snapshots and governed export jobs.

Revision ID: 20261009_0006
Revises: 20261009_0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261009_0006"
down_revision: str | None = "20261009_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "selection_table_snapshots",
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("schema_version", sa.String(80), nullable=False),
        sa.Column(
            "filters_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "store_scope_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("requested_by", sa.Uuid(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("snapshot_checksum", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("row_count >= 0", name="ck_selection_snapshot_row_count"),
        sa.PrimaryKeyConstraint("snapshot_id"),
    )
    op.create_index(
        "ix_selection_table_snapshots_stage", "selection_table_snapshots", ["stage"]
    )
    op.create_index(
        "ix_selection_table_snapshots_requested_by",
        "selection_table_snapshots",
        ["requested_by"],
    )
    op.create_table(
        "selection_table_snapshot_rows",
        sa.Column("snapshot_row_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("row_position", sa.Integer(), nullable=False),
        sa.Column("selection_id", sa.Uuid(), nullable=False),
        sa.Column("selection_revision", sa.Integer(), nullable=False),
        sa.Column(
            "rendered_row", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.CheckConstraint("row_position > 0", name="ck_selection_snapshot_row_position"),
        sa.ForeignKeyConstraint(
            ["selection_id"], ["selection_records.selection_id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"], ["selection_table_snapshots.snapshot_id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("snapshot_row_id"),
        sa.UniqueConstraint(
            "snapshot_id", "row_position", name="uq_selection_snapshot_row_position"
        ),
        sa.UniqueConstraint(
            "snapshot_id", "selection_id", name="uq_selection_snapshot_selection"
        ),
    )
    op.create_index(
        "ix_selection_table_snapshot_rows_snapshot_id",
        "selection_table_snapshot_rows",
        ["snapshot_id"],
    )
    op.create_index(
        "ix_selection_table_snapshot_rows_selection_id",
        "selection_table_snapshot_rows",
        ["selection_id"],
    )
    op.create_table(
        "selection_export_jobs",
        sa.Column("export_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(80), nullable=False),
        sa.Column(
            "filters_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "store_scope_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("requested_by", sa.Uuid(), nullable=False),
        sa.Column("authorization_revision", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("row_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("file_name", sa.String(255)),
        sa.Column("file_path", sa.String(1024)),
        sa.Column("file_checksum", sa.String(64)),
        sa.Column("error_code", sa.String(80)),
        sa.Column("error_message", sa.String(500)),
        sa.Column("trace_id", sa.String(120)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("row_count >= 0", name="ck_selection_export_row_count"),
        sa.CheckConstraint(
            "status IN ('queued','running','completed','failed')",
            name="ck_selection_export_status",
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"], ["selection_table_snapshots.snapshot_id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("export_id"),
    )
    for column in ("stage", "snapshot_id", "requested_by", "status", "trace_id"):
        op.create_index(
            f"ix_selection_export_jobs_{column}", "selection_export_jobs", [column]
        )
    op.execute(
        "INSERT INTO iam_permissions (permission_name, description) "
        "VALUES ('selection.export', 'Export frozen selection snapshots') "
        "ON CONFLICT DO NOTHING"
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM iam_user_permissions WHERE permission_name = 'selection.export'"
    )
    op.execute(
        "DELETE FROM iam_role_permissions WHERE permission_name = 'selection.export'"
    )
    op.execute("DELETE FROM iam_permissions WHERE permission_name = 'selection.export'")
    op.drop_table("selection_export_jobs")
    op.drop_table("selection_table_snapshot_rows")
    op.drop_table("selection_table_snapshots")
