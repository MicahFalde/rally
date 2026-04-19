import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import SurveyCreate, SurveyResponse
from app.core.database import get_db
from app.core.deps import require_organizer, require_volunteer
from app.models import CampaignMember, Survey, SurveyQuestion

router = APIRouter(prefix="/campaigns/{campaign_id}/surveys", tags=["surveys"])


@router.post("", response_model=SurveyResponse, status_code=status.HTTP_201_CREATED)
async def create_survey(
    campaign_id: uuid.UUID,
    data: SurveyCreate,
    member: CampaignMember = Depends(require_organizer),
    db: AsyncSession = Depends(get_db),
):
    survey = Survey(
        campaign_id=campaign_id,
        name=data.name,
        description=data.description,
    )
    db.add(survey)
    await db.flush()

    for q_data in data.questions:
        question = SurveyQuestion(
            survey_id=survey.id,
            question_text=q_data.question_text,
            question_key=q_data.question_key,
            order=q_data.order,
            options=q_data.options,
        )
        db.add(question)

    await db.commit()

    # Re-fetch with questions loaded
    result = await db.execute(
        select(Survey)
        .options(selectinload(Survey.questions))
        .where(Survey.id == survey.id)
    )
    return result.scalar_one()


@router.get("", response_model=list[SurveyResponse])
async def list_surveys(
    campaign_id: uuid.UUID,
    member: CampaignMember = Depends(require_volunteer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Survey)
        .options(selectinload(Survey.questions))
        .where(Survey.campaign_id == campaign_id, Survey.is_active == True)
        .order_by(Survey.name)
    )
    return result.scalars().all()


@router.get("/{survey_id}", response_model=SurveyResponse)
async def get_survey(
    campaign_id: uuid.UUID,
    survey_id: uuid.UUID,
    member: CampaignMember = Depends(require_volunteer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Survey)
        .options(selectinload(Survey.questions))
        .where(Survey.id == survey_id, Survey.campaign_id == campaign_id)
    )
    survey = result.scalar_one_or_none()
    if survey is None:
        raise HTTPException(status_code=404, detail="Survey not found")
    return survey
