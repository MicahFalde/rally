import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class VolunteerContact(UUIDMixin, TimestampMixin, Base):
    """A matched contact from a volunteer's phone — the relational organizing graph."""

    __tablename__ = "volunteer_contacts"

    volunteer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    voter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("voters.id"), nullable=False
    )

    # How they know each other (optional, volunteer-provided)
    relationship_type: Mapped[str | None] = mapped_column(String(50))  # friend/family/neighbor/coworker

    # Has the volunteer reached out through relational organizing?
    contacted: Mapped[bool] = mapped_column(default=False)
    contact_result: Mapped[str | None] = mapped_column(String(50))  # same support levels


class PrecinctNote(UUIDMixin, TimestampMixin, Base):
    """Shared operational knowledge about a precinct — persists across campaigns."""

    __tablename__ = "precinct_notes"

    state: Mapped[str] = mapped_column(String(2), nullable=False)
    precinct: Mapped[str] = mapped_column(String(50), nullable=False)

    # Who wrote it
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False
    )

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # Categories: access (gated communities, dogs), language, best_method (canvass vs text),
    # timing (best hours), parking, safety, apartment_codes, etc.

    note: Mapped[str] = mapped_column(Text, nullable=False)
