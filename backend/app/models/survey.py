import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Survey(UUIDMixin, TimestampMixin, Base):
    """A configurable survey/script for a campaign's canvass or phone bank."""

    __tablename__ = "surveys"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "Door Knock - Persuasion"
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)

    campaign = relationship("Campaign", back_populates="surveys")
    questions = relationship(
        "SurveyQuestion", back_populates="survey", cascade="all, delete-orphan",
        order_by="SurveyQuestion.order"
    )


class SurveyQuestion(UUIDMixin, Base):
    """A single question in a survey with predefined answer options."""

    __tablename__ = "survey_questions"

    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("surveys.id"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_key: Mapped[str] = mapped_column(String(50), nullable=False)  # used in survey_responses JSON
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Options as JSON array: [{"value": "strong_support", "label": "Strong Support"}, ...]
    options: Mapped[dict] = mapped_column(JSONB, nullable=False)

    survey = relationship("Survey", back_populates="questions")
