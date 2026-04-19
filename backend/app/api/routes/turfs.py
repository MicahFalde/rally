import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import TurfAssign, TurfCreate, TurfResponse
from app.core.database import get_db
from app.core.deps import require_organizer, require_volunteer
from app.models import CampaignMember, CampaignVoter, Turf, TurfVoter

router = APIRouter(prefix="/campaigns/{campaign_id}/turfs", tags=["turfs"])


@router.post("", response_model=TurfResponse, status_code=status.HTTP_201_CREATED)
async def create_turf(
    campaign_id: uuid.UUID,
    data: TurfCreate,
    member: CampaignMember = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    """Create a turf from a list of campaign voter IDs."""
    turf = Turf(
        campaign_id=campaign_id,
        name=data.name,
        description=data.description,
        total_doors=len(data.voter_ids),
    )
    db.add(turf)
    await db.flush()

    # Add voters to turf with walk order
    for order, cv_id in enumerate(data.voter_ids, 1):
        # Verify the campaign voter belongs to this campaign
        result = await db.execute(
            select(CampaignVoter).where(
                CampaignVoter.id == cv_id,
                CampaignVoter.campaign_id == campaign_id,
            )
        )
        cv = result.scalar_one_or_none()
        if cv is None:
            continue

        tv = TurfVoter(
            turf_id=turf.id,
            campaign_voter_id=cv_id,
            walk_order=order,
        )
        db.add(tv)

    await db.commit()
    await db.refresh(turf)
    return turf


@router.get("", response_model=list[TurfResponse])
async def list_turfs(
    campaign_id: uuid.UUID,
    member: CampaignMember = Depends(require_volunteer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Turf)
        .where(Turf.campaign_id == campaign_id)
        .order_by(Turf.name)
    )
    return result.scalars().all()


@router.get("/mine", response_model=list[TurfResponse])
async def list_my_turfs(
    campaign_id: uuid.UUID,
    member: CampaignMember = Depends(require_volunteer),
    db: AsyncSession = Depends(get_db),
):
    """Get turfs assigned to the current volunteer."""
    result = await db.execute(
        select(Turf).where(
            Turf.campaign_id == campaign_id,
            Turf.assigned_to_id == member.user_id,
            Turf.completed_at.is_(None),
        )
    )
    return result.scalars().all()


@router.post("/{turf_id}/assign", response_model=TurfResponse)
async def assign_turf(
    campaign_id: uuid.UUID,
    turf_id: uuid.UUID,
    data: TurfAssign,
    member: CampaignMember = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Turf).where(Turf.id == turf_id, Turf.campaign_id == campaign_id)
    )
    turf = result.scalar_one_or_none()
    if turf is None:
        raise HTTPException(status_code=404, detail="Turf not found")

    turf.assigned_to_id = data.volunteer_id
    turf.assigned_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(turf)
    return turf


@router.get("/{turf_id}/voters")
async def get_turf_voters(
    campaign_id: uuid.UUID,
    turf_id: uuid.UUID,
    member: CampaignMember = Depends(require_volunteer),
    db: AsyncSession = Depends(get_db),
):
    """Get the walk list for a turf — ordered voter list with addresses and survey info.
    This is what the mobile app downloads for offline canvassing."""
    result = await db.execute(
        select(TurfVoter)
        .options(
            selectinload(TurfVoter.campaign_voter).selectinload(CampaignVoter.voter)
        )
        .where(TurfVoter.turf_id == turf_id)
        .order_by(TurfVoter.walk_order)
    )
    turf_voters = result.scalars().all()

    walk_list = []
    for tv in turf_voters:
        cv = tv.campaign_voter
        v = cv.voter
        walk_list.append({
            "walk_order": tv.walk_order,
            "campaign_voter_id": str(cv.id),
            "voter_id": str(v.id),
            "first_name": v.first_name,
            "last_name": v.last_name,
            "address_line1": v.address_line1,
            "address_line2": v.address_line2,
            "city": v.city,
            "zip_code": v.zip_code,
            "party": v.party,
            "age": None,  # computed from DOB if needed
            "vote_history_count": len(v.vote_history) if v.vote_history else 0,
            "turnout_score": v.turnout_score,
            "current_support_level": cv.support_level,
            "latitude": None,  # extracted from PostGIS point if needed
            "longitude": None,
        })

    return {"turf_id": str(turf_id), "voters": walk_list}
