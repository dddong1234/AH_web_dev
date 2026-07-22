from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base


class AIAnalysisResult(Base):
    __tablename__ = "ai_analysis_results"
    __table_args__ = (
        UniqueConstraint(
            "record_id",
            "ai_model",
            name="uq_ai_analysis_record_model",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    record_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("medical_records.id", ondelete="CASCADE"),
        nullable=False,
    )

    is_pneumonia: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    heatmap_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ai_model: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("current_timestamp(0)"),
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        server_default=text("current_timestamp(0)"),
        onupdate=text("current_timestamp(0)"),
    )

    record = relationship(
        "MedicalRecord",
        back_populates="ai_analysis_results",
    )
