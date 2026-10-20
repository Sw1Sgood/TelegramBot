"""Реферальная программа: бонусы за друзей, которые сделали первый расклад."""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import repo
from app.db.models import User

FRIEND_READING_BONUS = 3


def referral_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start=ref_{user_id}"


async def reward_for_first_reading(session: AsyncSession, user: User) -> int | None:
    """Начисляет пригласившему бонус за первый расклад друга — один раз.

    Возвращает id пригласившего, если бонус начислен сейчас.
    """
    if user.referrer_id is None:
        return None
    referral = await repo.get_referral_by_referred(session, user.id)
    if referral is None or referral.rewarded_at is not None:
        return None
    referral.rewarded_at = datetime.now(timezone.utc)
    referral.reward_type = f"credits_{FRIEND_READING_BONUS}"
    await repo.add_credits(session, referral.referrer_id, FRIEND_READING_BONUS)
    await repo.log_event(session, referral.referrer_id, "referral_rewarded", {"referred_id": user.id})
    return referral.referrer_id
