from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import repo
from app.db.models import User


async def is_premium(session: AsyncSession, user: User, settings: Settings) -> bool:
    if settings.premium_for_all:
        return True
    return await repo.has_active_subscription(session, user.id, datetime.now(timezone.utc))
