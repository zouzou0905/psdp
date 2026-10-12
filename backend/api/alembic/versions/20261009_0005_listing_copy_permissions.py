"""Make Listing copy permissions operations-only by default.

Revision ID: 20261009_0005
Revises: 20261008_0004
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261009_0005"
down_revision: str | None = "20261008_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LISTING_COPY_PERMISSIONS = (
    "listing_copy.read",
    "listing_copy.generate",
    "listing_copy.edit",
    "listing_copy.review",
    "listing_copy.history.read",
)


def upgrade() -> None:
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
        [
            {"permission_name": permission, "description": permission}
            for permission in LISTING_COPY_PERMISSIONS
        ],
    )
    op.execute(
        "DELETE FROM iam_role_permissions "
        "WHERE permission_name IN ('listing.read', 'listing.draft')"
    )
    op.bulk_insert(
        role_permissions,
        [
            {"role_name": "operations", "permission_name": permission}
            for permission in LISTING_COPY_PERMISSIONS
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM iam_role_permissions WHERE permission_name IN "
        "('listing_copy.read','listing_copy.generate','listing_copy.edit',"
        "'listing_copy.review','listing_copy.history.read')"
    )
    op.execute(
        "DELETE FROM iam_permissions WHERE permission_name IN "
        "('listing_copy.read','listing_copy.generate','listing_copy.edit',"
        "'listing_copy.review','listing_copy.history.read')"
    )
    op.execute(
        "INSERT INTO iam_role_permissions (role_name, permission_name) VALUES "
        "('operations','listing.read'),('operations','listing.draft'),"
        "('admin','listing.read'),('admin','listing.draft') ON CONFLICT DO NOTHING"
    )
