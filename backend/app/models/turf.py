import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Turf(UUIDMixin, TimestampMixin, Base):
    """A walkable territory of 50-150 doors assigned to a volunteer."""

    __tablename__ = "turfs"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Precinct 5 - North"
    description: Mapped[str | None] = mapped_column(Text)

    # Geographic boundary (PostGIS polygon)
    boundary: Mapped[str | None] = mapped_column(Geometry("POLYGON", srid=4326))

    # Stats
    total_doors: Mapped[int] = mapped_column(Integer, default=0)
    doors_knocked: Mapped[int] = mapped_column(Integer, default=0)
    contacts_made: Mapped[int] = mapped_column(Integer, default=0)

    # Assignment
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    campaign = relationship("Campaign", back_populates="turfs")
    assigned_to = relationship("User")
    voters = relationship("TurfVoter", back_populates="turf", cascade="all, delete-orphan")


class TurfVoter(UUIDMixin, Base):
    """Links voters to a turf with a walk order."""

    __tablename__ = "turf_voters"

    turf_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("turfs.id"), nullable=False
    )
    campaign_voter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaign_voters.id"), nullable=False
    )
    walk_order: Mapped[int] = mapped_column(Integer, nullable=False)

    turf = relationship("Turf", back_populates="voters")
    campaign_voter = relationship("CampaignVoter")
