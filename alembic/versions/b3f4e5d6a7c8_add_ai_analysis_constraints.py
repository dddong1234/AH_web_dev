"""add AI analysis constraints for stage 6

Revision ID: b3f4e5d6a7c8
Revises: 4b7a9b4b6d22
Create Date: 2026-07-22 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3f4e5d6a7c8"
down_revision: Union[str, Sequence[str], None] = "4b7a9b4b6d22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _record_foreign_key_name() -> str:
    inspector = sa.inspect(op.get_bind())
    for foreign_key in inspector.get_foreign_keys("ai_analysis_results"):
        if (
            foreign_key.get("referred_table") == "medical_records"
            and foreign_key.get("constrained_columns") == ["record_id"]
        ):
            name = foreign_key.get("name")
            if isinstance(name, str):
                return name
    raise RuntimeError("record_id foreign key was not found")


def upgrade() -> None:
    op.drop_constraint(
        _record_foreign_key_name(),
        "ai_analysis_results",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_ai_analysis_results_record_id",
        "ai_analysis_results",
        "medical_records",
        ["record_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_ai_analysis_record_model",
        "ai_analysis_results",
        ["record_id", "ai_model"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_ai_analysis_record_model",
        "ai_analysis_results",
        type_="unique",
    )
    op.drop_constraint(
        "fk_ai_analysis_results_record_id",
        "ai_analysis_results",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_ai_analysis_results_record_id_no_cascade",
        "ai_analysis_results",
        "medical_records",
        ["record_id"],
        ["id"],
    )
