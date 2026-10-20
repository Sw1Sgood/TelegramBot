from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Event, Referral, User


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def add_user(session: AsyncSession, user: User) -> User:
    session.add(user)
    await session.flush()
    return user


async def delete_user(session: AsyncSession, user_id: int) -> None:
    # Связанные строки удаляются каскадом на уровне БД (ondelete=CASCADE).
    await session.execute(delete(User).where(User.id == user_id))
    session.expunge_all()


async def add_referral(session: AsyncSession, referrer_id: int, referred_id: int) -> Referral:
    referral = Referral(referrer_id=referrer_id, referred_id=referred_id)
    session.add(referral)
    await session.flush()
    return referral


async def get_referral_by_referred(session: AsyncSession, referred_id: int) -> Referral | None:
    result = await session.execute(select(Referral).where(Referral.referred_id == referred_id))
    return result.scalar_one_or_none()


async def log_event(session: AsyncSession, user_id: int | None, name: str, payload: dict[str, Any] | None = None) -> None:
    session.add(Event(user_id=user_id, name=name, payload=payload, created_at=datetime.now(timezone.utc)))
