"""Create primary_duty_configs table.

Replaces Airtable JSON export with DB-backed primary duty configuration.
Seeds from sanitized_primary_duties.json if available.

Revision ID: 20260314_primary_duty_tbl
Revises: 20260314_rt_preload_cols
Create Date: 2026-03-14
"""

import json
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260314_primary_duty_tbl"
down_revision = "20260314_rt_preload_cols"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "primary_duty_configs",
        sa.Column("id", sa.dialects.postgresql.UUID(), primary_key=True),
        sa.Column("duty_name", sa.String(100), nullable=False, unique=True),
        sa.Column(
            "clinic_min_per_week", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "clinic_max_per_week", sa.Integer(), nullable=False, server_default="10"
        ),
        sa.Column(
            "available_days", JSONB(), nullable=False, server_default="[0,1,2,3,4]"
        ),
        sa.Column("faculty_ids", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_primary_duty_configs_name", "primary_duty_configs", ["duty_name"]
    )

    # Seed from JSON if available
    json_path = (
        Path(__file__).parents[2]
        / "docs"
        / "schedules"
        / "sanitized_primary_duties.json"
    )
    if not json_path.exists():
        # Try relative from backend root
        json_path = (
            Path(__file__).parents[3]
            / "docs"
            / "schedules"
            / "sanitized_primary_duties.json"
        )

    if json_path.exists():
        with open(json_path) as f:
            data = json.load(f)

        for record in data.get("records", []):
            fields = record.get("fields", {})
            duty_name = fields.get("primaryDuty", "")
            if not duty_name:
                continue

            # Parse available days
            day_mapping = {
                "availableMonday": 0,
                "availableTuesday": 1,
                "availableWednesday": 2,
                "availableThursday": 3,
                "availableFriday": 4,
            }
            available = [
                day_num
                for field_name, day_num in day_mapping.items()
                if fields.get(field_name, False)
            ]
            if not available:
                available = [0, 1, 2, 3, 4]

            clinic_min = fields.get("Clinic Minimum Half-Days Per Week", 0)
            clinic_max = fields.get("Clinic Maximum Half-Days Per Week", 10)

            days_json = json.dumps(available)
            op.execute(
                sa.text(
                    "INSERT INTO primary_duty_configs "
                    "(id, duty_name, clinic_min_per_week, clinic_max_per_week, available_days) "
                    f"VALUES (gen_random_uuid(), :name, :cmin, :cmax, '{days_json}'::jsonb) "
                    "ON CONFLICT (duty_name) DO NOTHING"
                ).bindparams(
                    name=duty_name,
                    cmin=clinic_min,
                    cmax=clinic_max,
                )
            )


def downgrade() -> None:
    op.drop_index("ix_primary_duty_configs_name")
    op.drop_table("primary_duty_configs")
