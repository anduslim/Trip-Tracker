"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-04-25

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_init"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "holidays",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("destinations", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("notes", sa.Text),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("price_change_threshold_pct", sa.Numeric(5, 2)),
        sa.Column("price_change_threshold_abs", sa.Numeric(10, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_holidays_user_id", "holidays", ["user_id"])

    op.create_table(
        "flight_entries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("holiday_id", sa.Integer, sa.ForeignKey("holidays.id", ondelete="CASCADE"), nullable=False),
        sa.Column("origin_iata", sa.String(3), nullable=False),
        sa.Column("destination_iata", sa.String(3), nullable=False),
        sa.Column("depart_date", sa.Date, nullable=False),
        sa.Column("return_date", sa.Date),
        sa.Column("airline_code", sa.String(3)),
        sa.Column("airline_name", sa.String(100)),
        sa.Column("cabin", sa.String(20)),
        sa.Column("passengers", sa.Integer, nullable=False, server_default="1"),
        sa.Column("source_url", sa.Text),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("provider_offer_id", sa.String(100)),
        sa.Column("provider_offer_payload", sa.JSON),
        sa.Column("initial_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("latest_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("tracking_enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
        sa.Column("archived", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_flight_entries_holiday_id", "flight_entries", ["holiday_id"])
    op.create_index("ix_flight_entries_route", "flight_entries", ["origin_iata", "destination_iata"])

    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("flight_entry_id", sa.Integer, sa.ForeignKey("flight_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("raw_payload", sa.JSON),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_price_snapshots_flight_entry_id", "price_snapshots", ["flight_entry_id"])
    op.create_index("ix_price_snapshots_entry_captured", "price_snapshots", ["flight_entry_id", "captured_at"])


def downgrade() -> None:
    op.drop_index("ix_price_snapshots_entry_captured", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_flight_entry_id", table_name="price_snapshots")
    op.drop_table("price_snapshots")
    op.drop_index("ix_flight_entries_route", table_name="flight_entries")
    op.drop_index("ix_flight_entries_holiday_id", table_name="flight_entries")
    op.drop_table("flight_entries")
    op.drop_index("ix_holidays_user_id", table_name="holidays")
    op.drop_table("holidays")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
