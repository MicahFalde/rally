import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr


# --- Auth ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None
    zip_code: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    platform_role: str
    zip_code: str | None
    discoverable: bool
    total_doors_knocked: int
    total_contacts_made: int
    total_campaigns: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Campaigns ---

class CampaignCreate(BaseModel):
    name: str
    state: str  # 2-letter code
    district: str | None = None
    description: str | None = None


class CampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    state: str
    district: str | None
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignMemberAdd(BaseModel):
    email: str
    role: str  # campaign_admin, organizer, volunteer


class CampaignMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    campaign_id: uuid.UUID
    role: str
    is_active: bool
    doors_knocked: int
    contacts_made: int
    hours_volunteered: float
    user: UserResponse | None = None

    model_config = {"from_attributes": True}


# --- Voters ---

class VoterResponse(BaseModel):
    id: uuid.UUID
    state_voter_id: str
    state: str
    first_name: str
    last_name: str
    address_line1: str
    city: str
    zip_code: str
    county: str | None
    party: str | None
    state_house_district: str | None
    precinct: str | None
    turnout_score: float | None
    partisanship_score: float | None
    persuadability_score: float | None

    model_config = {"from_attributes": True}


class VoterListFilter(BaseModel):
    state_house_district: str | None = None
    precinct: str | None = None
    party: str | None = None
    min_turnout_score: float | None = None
    max_turnout_score: float | None = None
    min_persuadability_score: float | None = None
    voter_status: str | None = "active"
    zip_code: str | None = None
    county: str | None = None
    limit: int = 100
    offset: int = 0


# --- Turfs ---

class TurfCreate(BaseModel):
    name: str
    description: str | None = None
    voter_ids: list[uuid.UUID]  # campaign_voter IDs to include


class TurfResponse(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    name: str
    description: str | None
    total_doors: int
    doors_knocked: int
    contacts_made: int
    assigned_to_id: uuid.UUID | None
    assigned_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TurfAssign(BaseModel):
    volunteer_id: uuid.UUID


# --- Contact Results ---

class ContactResultCreate(BaseModel):
    campaign_voter_id: uuid.UUID
    turf_id: uuid.UUID | None = None
    contact_method: str
    disposition: str
    survey_responses: dict | None = None
    support_level: str | None = None
    volunteer_prospect: bool = False
    yard_sign_request: bool = False
    vote_by_mail_interest: bool = False
    notes: str | None = None
    client_timestamp: datetime | None = None


class ContactResultResponse(BaseModel):
    id: uuid.UUID
    campaign_voter_id: uuid.UUID
    volunteer_id: uuid.UUID
    turf_id: uuid.UUID | None
    contact_method: str
    disposition: str
    survey_responses: dict | None
    support_level: str | None
    notes: str | None
    contacted_at: datetime
    client_timestamp: datetime | None

    model_config = {"from_attributes": True}


class ContactResultBatch(BaseModel):
    """For offline sync — submit multiple contact results at once."""
    results: list[ContactResultCreate]


# --- Surveys ---

class SurveyQuestionCreate(BaseModel):
    question_text: str
    question_key: str
    order: int
    options: list[dict]  # [{"value": "strong_support", "label": "Strong Support"}, ...]


class SurveyCreate(BaseModel):
    name: str
    description: str | None = None
    questions: list[SurveyQuestionCreate]


class SurveyQuestionResponse(BaseModel):
    id: uuid.UUID
    question_text: str
    question_key: str
    order: int
    options: list[dict]

    model_config = {"from_attributes": True}


class SurveyResponse(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    questions: list[SurveyQuestionResponse]

    model_config = {"from_attributes": True}


# --- Analytics ---

class CampaignStats(BaseModel):
    total_voters_in_universe: int
    total_doors_knocked: int
    total_contacts_made: int
    contact_rate: float  # contacts / doors knocked
    support_breakdown: dict  # {"strong_support": 120, "lean_support": 80, ...}
    total_volunteers: int
    total_turfs: int
    turfs_completed: int
