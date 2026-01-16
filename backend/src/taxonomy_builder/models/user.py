"""User model for authenticated users."""

from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from taxonomy_builder.database import Base


class User(Base):
    """A user authenticated via Keycloak.

    This is a thin local record that stores the minimum needed for FK references.
    The source of truth for user identity is Keycloak.
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    keycloak_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
