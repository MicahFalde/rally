import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import VoterListFilter, VoterResponse
from app.core.database import get_db
from app.core.deps import require_campaign_admin, require_organizer
from app.models import CampaignMember, CampaignVoter, Voter

router = APIRouter(prefix="/campaigns/{campaign_id}/voters", tags=["voters"])


@router.get("", response_model=list[VoterResponse])
async def list_voters(
    campaign_id: uuid.UUID,
    state_house_district: str | None = None,
    precinct: str | None = None,
    party: str | None = None,
    min_turnout_score: float | None = None,
    max_turnout_score: float | None = None,
    min_persuadability_score: float | None = None,
    voter_status: str = "active",
    zip_code: str | None = None,
    county: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    member: CampaignMember = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    """List/filter voters. For organizers building target lists."""
    query = select(Voter).where(Voter.voter_status == voter_status)

    if state_house_district:
        query = query.where(Voter.state_house_district == state_house_district)
    if precinct:
        query = query.where(Voter.precinct == precinct)
    if party:
        query = query.where(Voter.party == party)
    if min_turnout_score is not None:
        query = query.where(Voter.turnout_score >= min_turnout_score)
    if max_turnout_score is not None:
        query = query.where(Voter.turnout_score <= max_turnout_score)
    if min_persuadability_score is not None:
        query = query.where(Voter.persuadability_score >= min_persuadability_score)
    if zip_code:
        query = query.where(Voter.zip_code == zip_code)
    if county:
        query = query.where(Voter.county == county.upper())

    query = query.order_by(Voter.last_name, Voter.first_name).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/target", status_code=status.HTTP_201_CREATED)
async def add_voters_to_target_universe(
    campaign_id: uuid.UUID,
    voter_ids: list[uuid.UUID],
    member: CampaignMember = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    """Add voters to this campaign's target universe."""
    added = 0
    for voter_id in voter_ids:
        # Check voter exists
        voter = await db.get(Voter, voter_id)
        if voter is None:
            continue

        # Check not already in campaign
        existing = await db.execute(
            select(CampaignVoter).where(
                CampaignVoter.campaign_id == campaign_id,
                CampaignVoter.voter_id == voter_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        cv = CampaignVoter(
            campaign_id=campaign_id,
            voter_id=voter_id,
            in_target_universe=True,
        )
        db.add(cv)
        added += 1

    await db.commit()
    return {"added": added, "total_requested": len(voter_ids)}


@router.post("/target/filter", status_code=status.HTTP_201_CREATED)
async def add_voters_by_filter(
    campaign_id: uuid.UUID,
    filters: VoterListFilter,
    member: CampaignMember = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    """Add all voters matching a filter to the target universe. This is the main list-building tool."""
    query = select(Voter.id).where(Voter.voter_status == (filters.voter_status or "active"))

    if filters.state_house_district:
        query = query.where(Voter.state_house_district == filters.state_house_district)
    if filters.precinct:
        query = query.where(Voter.precinct == filters.precinct)
    if filters.party:
        query = query.where(Voter.party == filters.party)
    if filters.min_turnout_score is not None:
        query = query.where(Voter.turnout_score >= filters.min_turnout_score)
    if filters.max_turnout_score is not None:
        query = query.where(Voter.turnout_score <= filters.max_turnout_score)
    if filters.min_persuadability_score is not None:
        query = query.where(Voter.persuadability_score >= filters.min_persuadability_score)
    if filters.zip_code:
        query = query.where(Voter.zip_code == filters.zip_code)
    if filters.county:
        query = query.where(Voter.county == filters.county.upper())

    result = await db.execute(query)
    voter_ids = result.scalars().all()

    added = 0
    for voter_id in voter_ids:
        existing = await db.execute(
            select(CampaignVoter.id).where(
                CampaignVoter.campaign_id == campaign_id,
                CampaignVoter.voter_id == voter_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        cv = CampaignVoter(
            campaign_id=campaign_id,
            voter_id=voter_id,
            in_target_universe=True,
        )
        db.add(cv)
        added += 1

    await db.commit()
    return {"added": added, "total_matched": len(voter_ids)}
