"""Add submitted quotation status and quotation export permission.

Revision ID: 20261009_0007
Revises: 20261009_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261009_0007"
down_revision: str | None = "20261009_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "selection_quotation_versions",
        sa.Column(
            "submission_status",
            sa.String(24),
            server_default=sa.text("'submitted'"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_selection_quotation_submission_status",
        "selection_quotation_versions",
        "submission_status IN ('draft','submitted')",
    )
    op.execute(
        "INSERT INTO iam_permissions (permission_name, description) "
        "VALUES ('quotation.export', 'Export frozen submitted quotation snapshots') "
        "ON CONFLICT DO NOTHING"
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM iam_user_permissions WHERE permission_name = 'quotation.export'"
    )
    op.execute(
        "DELETE FROM iam_role_permissions WHERE permission_name = 'quotation.export'"
    )
    op.execute("DELETE FROM iam_permissions WHERE permission_name = 'quotation.export'")
    op.drop_constraint(
        "ck_selection_quotation_submission_status",
        "selection_quotation_versions",
        type_="check",
    )
    op.drop_column("selection_quotation_versions", "submission_status")
