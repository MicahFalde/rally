import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class AuditLog(UUIDMixin, Base):
    """Append-only audit trail. Every write to the system is logged here."""

    __tablename__ = "audit_log"

    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id")
    )

    action: Mapped[str] = mapped_column(String(50), nullable=False)  # create/update/delete
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # voter/contact_result/turf/etc
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # Snapshot of changes
    old_values: Mapped[dict | None] = mapped_column(JSONB)
    new_values: Mapped[dict | None] = mapped_column(JSONB)

    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
