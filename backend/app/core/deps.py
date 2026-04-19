import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import CampaignMember, CampaignRole, PlatformRole, User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def require_platform_admin(user: User = Depends(get_current_user)) -> User:
    if user.platform_role != PlatformRole.PLATFORM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required",
        )
    return user


class CampaignAccess:
    """Dependency that validates a user has a specific role in a campaign."""

    def __init__(self, min_role: CampaignRole = CampaignRole.VOLUNTEER):
        self.min_role = min_role
        self._role_hierarchy = {
            CampaignRole.CAMPAIGN_ADMIN: 3,
            CampaignRole.ORGANIZER: 2,
            CampaignRole.VOLUNTEER: 1,
        }

    async def __call__(
        self,
        campaign_id: uuid.UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> CampaignMember:
        # Platform admins bypass campaign role checks
        if user.platform_role == PlatformRole.PLATFORM_ADMIN:
            # Create a virtual membership for the admin
            result = await db.execute(
                select(CampaignMember).where(
                    CampaignMember.campaign_id == campaign_id,
                    CampaignMember.user_id == user.id,
                )
            )
            member = result.scalar_one_or_none()
            if member:
                return member
            # Return a synthetic admin membership
            return CampaignMember(
                user_id=user.id,
                campaign_id=campaign_id,
                role=CampaignRole.CAMPAIGN_ADMIN,
                is_active=True,
            )

        result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == user.id,
                CampaignMember.is_active == True,
            )
        )
        member = result.scalar_one_or_none()

        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this campaign",
            )

        if self._role_hierarchy[member.role] < self._role_hierarchy[self.min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {self.min_role.value} role or higher",
            )

        return member


# Pre-built dependency instances
require_volunteer = CampaignAccess(CampaignRole.VOLUNTEER)
require_organizer = CampaignAccess(CampaignRole.ORGANIZER)
require_campaign_admin = CampaignAccess(CampaignRole.CAMPAIGN_ADMIN)
