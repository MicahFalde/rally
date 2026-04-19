import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class PlatformRole(str, enum.Enum):
    PLATFORM_ADMIN = "platform_admin"
    USER = "user"


class CampaignRole(str, enum.Enum):
    CAMPAIGN_ADMIN = "campaign_admin"
    ORGANIZER = "organizer"
    VOLUNTEER = "volunteer"


class User(UUIDMixin, TimestampMixin, Base):
    """Persistent user identity — survives across campaigns."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    platform_role: Mapped[PlatformRole] = mapped_column(
        Enum(PlatformRole), default=PlatformRole.USER, nullable=False
    )

    # Persistent volunteer profile (network layer)
    bio: Mapped[str | None] = mapped_column(Text)
    zip_code: Mapped[str | None] = mapped_column(String(10))
    discoverable: Mapped[bool] = mapped_column(default=False)  # opt-in for future campaigns
    total_doors_knocked: Mapped[int] = mapped_column(default=0)
    total_contacts_made: Mapped[int] = mapped_column(default=0)
    total_campaigns: Mapped[int] = mapped_column(default=0)

    # Relationships
    campaign_memberships = relationship(
        "CampaignMember", back_populates="user", cascade="all, delete-orphan"
    )


class CampaignMember(UUIDMixin, TimestampMixin, Base):
    """Links a user to a campaign with a specific role."""

    __tablename__ = "campaign_members"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False
    )
    role: Mapped[CampaignRole] = mapped_column(Enum(CampaignRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Per-campaign volunteer stats
    doors_knocked: Mapped[int] = mapped_column(default=0)
    contacts_made: Mapped[int] = mapped_column(default=0)
    hours_volunteered: Mapped[float] = mapped_column(default=0.0)

    # Relationships
    user = relationship("User", back_populates="campaign_memberships")
    campaign = relationship("Campaign", back_populates="members")
