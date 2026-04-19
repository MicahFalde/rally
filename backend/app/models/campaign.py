from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Campaign(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)  # e.g. "OH"
    district: Mapped[str | None] = mapped_column(String(100))  # e.g. "OH-HD-15"
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    members = relationship("CampaignMember", back_populates="campaign", cascade="all, delete-orphan")
    turfs = relationship("Turf", back_populates="campaign", cascade="all, delete-orphan")
    surveys = relationship("Survey", back_populates="campaign", cascade="all, delete-orphan")
    campaign_voters = relationship(
        "CampaignVoter", back_populates="campaign", cascade="all, delete-orphan"
    )
