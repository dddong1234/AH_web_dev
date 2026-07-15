from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from .enums import Gender



class Patients(Base):
    __tablename__ = "patients"

    #환자 정보 테이블
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )
    # 환자 성명
    name: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    # 환자 나이
    age: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False
    )
    # 환자 성별Enum gender
    gender: Mapped[Gender] = mapped_column(
        Enum(Gender, name="gender"),
        nullable=False
    )


    # 환자 연락처, 국내 전화번호로 한정
    phone: Mapped[str] = mapped_column(
    String(11),
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
    medical_records = relationship(
        "MedicalRecord",
        back_populates="patient",
    )