"""notifications + share_tokens

Revision ID: 0002_notifications_share
Revises: 0001_init
Create Date: 2026-04-25
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_notifications_share"
down_revision: str | None = "0001_init"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("holiday_id", sa.Integer, sa.ForeignKey("holidays.id", ondelete="SET NULL")),
        sa.Column("flight_entry_id", sa.Integer, sa.ForeignKey("flight_entries.id", ondelete="SET NULL")),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("extra", sa.JSON),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("email_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("email_sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "read_at"])
    op.create_index("ix_notifications_email_status", "notifications", ["email_status"])

    op.create_table(
        "share_tokens",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("holiday_id", sa.Integer, sa.ForeignKey("holidays.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_share_tokens_token", "share_tokens", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_share_tokens_token", table_name="share_tokens")
    op.drop_table("share_tokens")
    op.drop_index("ix_notifications_email_status", table_name="notifications")
    op.drop_index("ix_notifications_user_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
