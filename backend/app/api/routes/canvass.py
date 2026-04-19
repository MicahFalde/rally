import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ContactResultBatch, ContactResultCreate, ContactResultResponse
from app.core.database import get_db
from app.core.deps import get_current_user, require_volunteer
from app.models import (
    CampaignMember,
    CampaignVoter,
    ContactMethod,
    ContactResult,
    Disposition,
    Turf,
    User,
)

router = APIRouter(prefix="/campaigns/{campaign_id}/canvass", tags=["canvass"])


async def _record_contact(
    data: ContactResultCreate,
    volunteer_id: uuid.UUID,
    campaign_id: uuid.UUID,
    db: AsyncSession,
) -> ContactResult:
    """Record a single contact result. Core logic shared by single and batch endpoints."""
    # Verify campaign_voter belongs to this campaign
    result = await db.execute(
        select(CampaignVoter).where(
            CampaignVoter.id == data.campaign_voter_id,
            CampaignVoter.campaign_id == campaign_id,
        )
    )
    cv = result.scalar_one_or_none()
    if cv is None:
        raise HTTPException(status_code=404, detail="Campaign voter not found")

    contact = ContactResult(
        campaign_voter_id=data.campaign_voter_id,
        volunteer_id=volunteer_id,
        turf_id=data.turf_id,
        contact_method=ContactMethod(data.contact_method),
        disposition=Disposition(data.disposition),
        survey_responses=data.survey_responses,
        support_level=data.support_level,
        volunteer_prospect=data.volunteer_prospect,
        yard_sign_request=data.yard_sign_request,
        vote_by_mail_interest=data.vote_by_mail_interest,
        notes=data.notes,
        client_timestamp=data.client_timestamp,
    )
    db.add(contact)

    # Update campaign voter with latest contact data
    if data.support_level:
        cv.support_level = data.support_level
    if data.volunteer_prospect:
        cv.volunteer_prospect = True
    if data.yard_sign_request:
        cv.yard_sign_request = True
    if data.vote_by_mail_interest:
        cv.vote_by_mail_interest = True

    # Update turf stats if applicable
    if data.turf_id:
        turf_result = await db.execute(select(Turf).where(Turf.id == data.turf_id))
        turf = turf_result.scalar_one_or_none()
        if turf:
            turf.doors_knocked += 1
            if data.disposition == Disposition.CONTACT.value:
                turf.contacts_made += 1

    return contact


@router.post("/results", response_model=ContactResultResponse, status_code=status.HTTP_201_CREATED)
async def record_contact(
    campaign_id: uuid.UUID,
    data: ContactResultCreate,
    member: CampaignMember = Depends(require_volunteer),
    db: AsyncSession = Depends(get_db),
):
    """Record a single contact result from canvassing."""
    contact = await _record_contact(data, member.user_id, campaign_id, db)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.post("/results/batch", status_code=status.HTTP_201_CREATED)
async def record_contacts_batch(
    campaign_id: uuid.UUID,
    data: ContactResultBatch,
    member: CampaignMember = Depends(require_volunteer),
    db: AsyncSession = Depends(get_db),
):
    """Batch submit contact results — used by the mobile app for offline sync.
    All results are applied in a single transaction."""
    recorded = 0
    errors = []

    for i, result_data in enumerate(data.results):
        try:
            await _record_contact(result_data, member.user_id, campaign_id, db)
            recorded += 1
        except HTTPException as e:
            errors.append({"index": i, "error": e.detail})

    await db.commit()
    return {"recorded": recorded, "errors": errors}
