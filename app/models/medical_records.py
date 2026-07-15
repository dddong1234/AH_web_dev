from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# 클래스
class MedicalRecord(Base):
    __tablename__="medical_records"

    # PK
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    # FK
    patient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("patients.id"),
        nullable=False
    )

    # 환자 진료차트 번호
    chart_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True
    )

    # 환자 증상기록
    symptoms: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # 환자 정보 등록 일시
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    # 환자 정보 수정일시
    updated_at: Mapped[datetime|None] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=func.now()
    )

    # 관계 연결
    patient = relationship(
        "Patient",
        back_populates="medical_records",
    )


