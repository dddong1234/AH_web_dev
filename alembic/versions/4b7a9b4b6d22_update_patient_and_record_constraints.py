"""update patient and record constraints for stage 5

Revision ID: 4b7a9b4b6d22
Revises: e6b2f166c001
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b7a9b4b6d22"
down_revision: Union[str, Sequence[str], None] = "e6b2f166c001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _find_patient_fk_name() -> str | None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    foreign_keys = inspector.get_foreign_keys("medical_records")

    for foreign_key in foreign_keys:
        if (
            foreign_key.get("referred_table") == "patients"
            and foreign_key.get("constrained_columns") == ["patient_id"]
        ):
            return foreign_key.get("name")
    return None


def upgrade() -> None:
    op.alter_column(
        "patients",
        "name",
        existing_type=sa.String(length=30),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
    op.alter_column(
        "patients",
        "phone",
        existing_type=sa.String(length=11),
        type_=sa.String(length=20),
        existing_nullable=False,
    )

    fk_name = _find_patient_fk_name()
    if fk_name is not None:
        op.drop_constraint(fk_name, "medical_records", type_="foreignkey")

    op.create_foreign_key(
        "fk_medical_records_patient_id_patients",
        "medical_records",
        "patients",
        ["patient_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_medical_records_patient_id_patients",
        "medical_records",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_medical_records_patient_id",
        "medical_records",
        "patients",
        ["patient_id"],
        ["id"],
    )

    op.alter_column(
        "patients",
        "phone",
        existing_type=sa.String(length=20),
        type_=sa.String(length=11),
        existing_nullable=False,
    )
    op.alter_column(
        "patients",
        "name",
        existing_type=sa.String(length=50),
        type_=sa.String(length=30),
        existing_nullable=False,
    )
