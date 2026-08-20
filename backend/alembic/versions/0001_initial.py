"""Révision initiale : tables `swagger_specs` et `generated_servers`.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "swagger_specs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("version", sa.String(64), nullable=True),
        sa.Column("openapi_version", sa.String(16), nullable=True),
        sa.Column("base_url", sa.String(512), nullable=True),
        sa.Column("endpoints_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "generated_servers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("base_url", sa.String(512), nullable=True),
        sa.Column("auth_type", sa.String(32), nullable=False, server_default="none"),
        sa.Column("auth_config", sa.Text(), nullable=True),
        sa.Column("endpoints", sa.Text(), nullable=True),
        sa.Column("endpoints_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.Enum("pending", "generating", "ready", "regenerating", "failed", name="serverstatus"), nullable=False),
        sa.Column("dir_name", sa.String(255), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("spec_id", sa.Integer(), sa.ForeignKey("swagger_specs.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_generated_servers_name", "generated_servers", ["name"])


def downgrade() -> None:
    op.drop_index("ix_generated_servers_name", table_name="generated_servers")
    op.drop_table("generated_servers")
    op.drop_table("swagger_specs")