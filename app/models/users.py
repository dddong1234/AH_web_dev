from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    String,
    func,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.core.db.databases import Base
from app.models.enums import (
    Department,
    Gender,
    Role,
)

if TYPE_CHECKING:
    from app.models.xray_image import XrayImage


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
    )

    gender: Mapped[Gender] = mapped_column(
        SQLEnum(
            Gender,
            name="gender",
        ),
        nullable=False,
    )

    department: Mapped[Department] = mapped_column(
        SQLEnum(
            Department,
            name="department",
        ),
        nullable=False,
    )

    role: Mapped[Role] = mapped_column(
        SQLEnum(
            Role,
            name="role",
        ),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=func.current_timestamp(),
    )

    xray_images: Mapped[list["XrayImage"]] = relationship(
        "XrayImage",
        back_populates="uploader",
        passive_deletes=True,
    )