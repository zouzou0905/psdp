"""Add account-derived modules, direct permissions and normalized store scopes.

Revision ID: 20261007_0003
Revises: 20261006_0002
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261007_0003"
down_revision: str | None = "20261006_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MODULES = ("operations", "procurement", "creative", "admin")
STORE_PERMISSIONS = ("store.read", "store.manage")


def upgrade() -> None:
    op.add_column(
        "iam_users",
        sa.Column(
            "authorization_revision",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    )
    op.create_table(
        "iam_modules",
        sa.Column("module_code", sa.String(64), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("module_code", name=op.f("pk_iam_modules")),
    )
    op.create_table(
        "stores",
        sa.Column("store_id", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("marketplace", sa.String(80), nullable=False),
        sa.Column("organization_id", sa.String(120), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("credential_ref", sa.String(255), nullable=True),
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
        sa.PrimaryKeyConstraint("store_id", name=op.f("pk_stores")),
    )
    op.create_index(op.f("ix_stores_organization_id"), "stores", ["organization_id"])
    op.create_index(op.f("ix_stores_status"), "stores", ["status"])
    op.create_table(
        "iam_user_modules",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("module_code", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["module_code"], ["iam_modules.module_code"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["iam_users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "module_code", name=op.f("pk_iam_user_modules")),
    )
    op.create_table(
        "iam_user_permissions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("permission_name", sa.String(120), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_name"], ["iam_permissions.permission_name"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["iam_users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "permission_name", name=op.f("pk_iam_user_permissions")),
    )
    op.create_table(
        "iam_user_store_scopes",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.store_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["iam_users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "store_id", name=op.f("pk_iam_user_store_scopes")),
    )
    _seed_and_migrate()
    op.drop_column("iam_users", "store_ids")


def _seed_and_migrate() -> None:
    modules = sa.table(
        "iam_modules", sa.column("module_code", sa.String), sa.column("description", sa.String)
    )
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
        modules,
        [{"module_code": value, "description": f"Built-in {value} module"} for value in MODULES],
    )
    op.bulk_insert(
        permissions,
        [{"permission_name": value, "description": value} for value in STORE_PERMISSIONS],
    )
    op.bulk_insert(
        role_permissions,
        [{"role_name": "admin", "permission_name": permission} for permission in STORE_PERMISSIONS],
    )
    op.execute(
        """
        INSERT INTO iam_user_modules (user_id, module_code)
        SELECT user_id, role_name FROM iam_user_roles
        WHERE role_name IN ('operations', 'procurement', 'creative')
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO iam_user_modules (user_id, module_code)
        SELECT roles.user_id, modules.module_code
        FROM iam_user_roles AS roles
        CROSS JOIN (
          VALUES ('operations'), ('procurement'), ('creative'), ('admin')
        ) AS modules(module_code)
        WHERE roles.role_name = 'admin'
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO stores
          (store_id, display_name, marketplace, organization_id, status, revision)
        SELECT DISTINCT store_id, store_id || ' (migrated)', 'unconfigured',
               'legacy', 'inactive', 1
        FROM iam_users,
             LATERAL jsonb_array_elements_text(store_ids) AS scope_store(store_id)
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO iam_user_store_scopes (user_id, store_id)
        SELECT user_id, store_id
        FROM iam_users,
             LATERAL jsonb_array_elements_text(store_ids) AS scope_store(store_id)
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.add_column(
        "iam_users",
        sa.Column(
            "store_ids",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.execute(
        """
        UPDATE iam_users AS users
        SET store_ids = scopes.store_ids
        FROM (
          SELECT user_id, jsonb_agg(store_id ORDER BY store_id) AS store_ids
          FROM iam_user_store_scopes GROUP BY user_id
        ) AS scopes
        WHERE users.user_id = scopes.user_id
        """
    )
    op.drop_table("iam_user_store_scopes")
    op.drop_table("iam_user_permissions")
    op.drop_table("iam_user_modules")
    op.drop_index(op.f("ix_stores_status"), table_name="stores")
    op.drop_index(op.f("ix_stores_organization_id"), table_name="stores")
    op.drop_table("stores")
    op.drop_table("iam_modules")
    op.execute(
        "DELETE FROM iam_role_permissions WHERE permission_name IN ('store.read', 'store.manage')"
    )
    op.execute(
        "DELETE FROM iam_permissions WHERE permission_name IN ('store.read', 'store.manage')"
    )
    op.drop_column("iam_users", "authorization_revision")
