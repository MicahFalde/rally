from fastapi import APIRouter, Depends
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User, Voter

router = APIRouter(prefix="/lookups", tags=["lookups"])


@router.get("/counties")
async def list_counties(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(distinct(Voter.county))
        .where(Voter.county.isnot(None))
        .order_by(Voter.county)
    )
    return [row[0] for row in result.all()]


@router.get("/districts")
async def list_districts(
    county: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(distinct(Voter.state_house_district))
        .where(Voter.state_house_district.isnot(None))
    )
    if county:
        query = query.where(Voter.county == county.upper())
    query = query.order_by(Voter.state_house_district)
    result = await db.execute(query)
    return [row[0] for row in result.all()]


@router.get("/precincts")
async def list_precincts(
    county: str | None = None,
    district: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(distinct(Voter.precinct))
        .where(Voter.precinct.isnot(None))
    )
    if county:
        query = query.where(Voter.county == county.upper())
    if district:
        query = query.where(Voter.state_house_district == district)
    query = query.order_by(Voter.precinct)
    result = await db.execute(query)
    return [row[0] for row in result.all()]
