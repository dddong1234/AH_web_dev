from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )

    chart_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    symptoms: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=func.now(),
    )

    patient = relationship(
        "Patients",
        back_populates="medical_records",
    )

    xray_images = relationship(
        "XrayImage",
        back_populates="record",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    ai_analysis_results = relationship(
        "AIAnalysisResult",
        back_populates="record",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
