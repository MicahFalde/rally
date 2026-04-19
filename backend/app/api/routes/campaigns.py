import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import (
    CampaignCreate,
    CampaignMemberAdd,
    CampaignMemberResponse,
    CampaignResponse,
    CampaignStats,
)
from app.core.database import get_db
from app.core.deps import get_current_user, require_campaign_admin, require_organizer
from app.models import (
    Campaign,
    CampaignMember,
    CampaignRole,
    CampaignVoter,
    ContactResult,
    Disposition,
    Turf,
    User,
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    campaign = Campaign(
        name=data.name,
        state=data.state.upper(),
        district=data.district,
        description=data.description,
    )
    db.add(campaign)
    await db.flush()

    # Creator becomes campaign admin
    member = CampaignMember(
        user_id=user.id,
        campaign_id=campaign.id,
        role=CampaignRole.CAMPAIGN_ADMIN,
    )
    db.add(member)

    # Update user's campaign count
    user.total_campaigns += 1

    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("", response_model=list[CampaignResponse])
async def list_my_campaigns(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign)
        .join(CampaignMember)
        .where(CampaignMember.user_id == user.id, CampaignMember.is_active == True)
        .order_by(Campaign.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    member: CampaignMember = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == member.campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("/{campaign_id}/members", response_model=CampaignMemberResponse)
async def add_member(
    campaign_id: uuid.UUID,
    data: CampaignMemberAdd,
    member: CampaignMember = Depends(require_campaign_admin),
    db: AsyncSession = Depends(get_db),
):
    # Find the user by email
    result = await db.execute(select(User).where(User.email == data.email))
    target_user = result.scalar_one_or_none()
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found with that email")

    # Check not already a member
    result = await db.execute(
        select(CampaignMember).where(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.user_id == target_user.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="User is already a campaign member")

    role = CampaignRole(data.role)
    new_member = CampaignMember(
        user_id=target_user.id,
        campaign_id=campaign_id,
        role=role,
    )
    db.add(new_member)
    target_user.total_campaigns += 1
    await db.commit()
    await db.refresh(new_member)
    return new_member


@router.get("/{campaign_id}/members", response_model=list[CampaignMemberResponse])
async def list_members(
    campaign_id: uuid.UUID,
    member: CampaignMember = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CampaignMember)
        .options(selectinload(CampaignMember.user))
        .where(CampaignMember.campaign_id == campaign_id)
        .order_by(CampaignMember.role)
    )
    return result.scalars().all()


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: uuid.UUID,
    member: CampaignMember = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    # Total voters in target universe
    voters_count = await db.scalar(
        select(func.count(CampaignVoter.id)).where(
            CampaignVoter.campaign_id == campaign_id,
            CampaignVoter.in_target_universe == True,
        )
    )

    # Contact results
    contact_results = await db.execute(
        select(ContactResult.disposition, func.count(ContactResult.id))
        .join(CampaignVoter)
        .where(CampaignVoter.campaign_id == campaign_id)
        .group_by(ContactResult.disposition)
    )
    disposition_counts = dict(contact_results.all())

    total_doors = sum(disposition_counts.values())
    total_contacts = disposition_counts.get(Disposition.CONTACT, 0)
    contact_rate = total_contacts / total_doors if total_doors > 0 else 0.0

    # Support breakdown
    support_results = await db.execute(
        select(ContactResult.support_level, func.count(ContactResult.id))
        .join(CampaignVoter)
        .where(
            CampaignVoter.campaign_id == campaign_id,
            ContactResult.support_level.isnot(None),
        )
        .group_by(ContactResult.support_level)
    )
    support_breakdown = dict(support_results.all())

    # Volunteers
    volunteer_count = await db.scalar(
        select(func.count(CampaignMember.id)).where(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.is_active == True,
        )
    )

    # Turfs
    turf_results = await db.execute(
        select(
            func.count(Turf.id),
            func.count(Turf.completed_at),
        ).where(Turf.campaign_id == campaign_id)
    )
    turf_row = turf_results.one()

    return CampaignStats(
        total_voters_in_universe=voters_count or 0,
        total_doors_knocked=total_doors,
        total_contacts_made=total_contacts,
        contact_rate=contact_rate,
        support_breakdown=support_breakdown,
        total_volunteers=volunteer_count or 0,
        total_turfs=turf_row[0] or 0,
        turfs_completed=turf_row[1] or 0,
    )
