import enum
import uuid
from datetime import date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Voter(UUIDMixin, TimestampMixin, Base):
    """Master voter record from state voter file. One per registered voter."""

    __tablename__ = "voters"

    # State voter file ID (unique per state)
    state_voter_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(2), nullable=False, index=True)  # "OH"

    # Identity
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    suffix: Mapped[str | None] = mapped_column(String(20))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(1))  # M/F/U

    # Address
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    county: Mapped[str | None] = mapped_column(String(100))

    # Geolocation (PostGIS point)
    location: Mapped[str | None] = mapped_column(Geometry("POINT", srid=4326))

    # Registration
    party: Mapped[str | None] = mapped_column(String(20), index=True)  # D/R/I/L/G/U
    registration_date: Mapped[date | None] = mapped_column(Date)
    voter_status: Mapped[str] = mapped_column(String(20), default="active")  # active/inactive

    # Districts
    congressional_district: Mapped[str | None] = mapped_column(String(20))
    state_senate_district: Mapped[str | None] = mapped_column(String(20))
    state_house_district: Mapped[str | None] = mapped_column(String(20), index=True)
    county_council_district: Mapped[str | None] = mapped_column(String(20))
    school_district: Mapped[str | None] = mapped_column(String(100))
    precinct: Mapped[str | None] = mapped_column(String(50), index=True)

    # Vote history — stored as JSON array of elections participated in
    # e.g. [{"election": "2024-11-GEN", "method": "in-person"}, ...]
    vote_history: Mapped[dict | None] = mapped_column(JSONB)

    # Enhanced data (from L2/TargetSmart or modeling)
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    modeled_ethnicity: Mapped[str | None] = mapped_column(String(50))
    modeled_income: Mapped[str | None] = mapped_column(String(50))
    modeled_education: Mapped[str | None] = mapped_column(String(50))
    turnout_score: Mapped[float | None] = mapped_column(Float)  # 0-100
    partisanship_score: Mapped[float | None] = mapped_column(Float)  # 0-100
    persuadability_score: Mapped[float | None] = mapped_column(Float)  # 0-100

    # Relationships
    campaign_voters = relationship("CampaignVoter", back_populates="voter")

    __table_args__ = (
        Index("ix_voters_state_voter_id", "state", "state_voter_id", unique=True),
        Index("ix_voters_name_dob", "last_name", "first_name", "date_of_birth"),
        # GeoAlchemy2 auto-creates a GIST index on 'location' as idx_voters_location
    )


class CampaignVoter(UUIDMixin, TimestampMixin, Base):
    """Campaign-specific voter targeting and contact data. Scoped to one campaign."""

    __tablename__ = "campaign_voters"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False
    )
    voter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("voters.id"), nullable=False
    )

    # Targeting
    in_target_universe: Mapped[bool] = mapped_column(default=False)
    priority: Mapped[int] = mapped_column(default=0)  # higher = more important to contact

    # Current support level (updated from most recent contact)
    support_level: Mapped[str | None] = mapped_column(String(20))  # strong_support/lean_support/undecided/lean_oppose/strong_oppose

    # Tags
    volunteer_prospect: Mapped[bool] = mapped_column(default=False)
    yard_sign_request: Mapped[bool] = mapped_column(default=False)
    vote_by_mail_interest: Mapped[bool] = mapped_column(default=False)

    # Custom tags as JSON
    tags: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    campaign = relationship("Campaign", back_populates="campaign_voters")
    voter = relationship("Voter", back_populates="campaign_voters")
    contact_results = relationship(
        "ContactResult", back_populates="campaign_voter", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_campaign_voters_campaign_voter", "campaign_id", "voter_id", unique=True),
    )


class ContactMethod(str, enum.Enum):
    DOOR_KNOCK = "door_knock"
    PHONE = "phone"
    TEXT = "text"
    RELATIONAL = "relational"  # friend-to-friend outreach


class Disposition(str, enum.Enum):
    CONTACT = "contact"  # successful conversation
    NOT_HOME = "not_home"
    REFUSED = "refused"
    MOVED = "moved"
    DECEASED = "deceased"
    INACCESSIBLE = "inaccessible"
    COME_BACK = "come_back"
    LANGUAGE_BARRIER = "language_barrier"
    HOSTILE = "hostile"
    WRONG_NUMBER = "wrong_number"
    VOICEMAIL = "voicemail"
    NO_ANSWER = "no_answer"


class ContactResult(UUIDMixin, Base):
    """Append-only log of every voter contact attempt. Never updated, never deleted."""

    __tablename__ = "contact_results"

    campaign_voter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaign_voters.id"), nullable=False
    )
    volunteer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    turf_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("turfs.id")
    )

    contact_method: Mapped[ContactMethod] = mapped_column(
        Enum(ContactMethod), nullable=False
    )
    disposition: Mapped[Disposition] = mapped_column(Enum(Disposition), nullable=False)

    # Survey responses — JSON object keyed by survey question ID
    # e.g. {"q1_support": "strong_support", "q2_issue": "education"}
    survey_responses: Mapped[dict | None] = mapped_column(JSONB)

    # Support level captured at this contact
    support_level: Mapped[str | None] = mapped_column(String(20))

    # Tags set during this contact
    volunteer_prospect: Mapped[bool] = mapped_column(default=False)
    yard_sign_request: Mapped[bool] = mapped_column(default=False)
    vote_by_mail_interest: Mapped[bool] = mapped_column(default=False)

    notes: Mapped[str | None] = mapped_column(Text)

    contacted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # For offline sync — the client-side timestamp when the contact happened
    client_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    campaign_voter = relationship("CampaignVoter", back_populates="contact_results")
    volunteer = relationship("User")
    turf = relationship("Turf")

    __table_args__ = (
        Index("ix_contact_results_campaign_voter", "campaign_voter_id"),
        Index("ix_contact_results_volunteer", "volunteer_id"),
        Index("ix_contact_results_contacted_at", "contacted_at"),
    )
