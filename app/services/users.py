import re
from dataclasses import dataclass
from datetime import date, datetime, time, timezone

from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import repo
from app.db.models import User
from app.services.astrology import zodiac_sign
from app.services.numerology import life_path_number

SUPPORTED_LANGUAGES = ("ru", "en")
# Языки, носителям которых по умолчанию удобнее русский интерфейс.
_RU_LANGUAGE_CODES = frozenset({"ru", "uk", "be", "kk", "uz", "ky", "tg", "hy", "az", "ka", "tk", "mo"})

_SOURCE_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def detect_language(language_code: str | None, default: str = "ru") -> str:
    if not language_code:
        return default
    base = language_code.split("-")[0].lower()
    if base in _RU_LANGUAGE_CODES:
        return "ru"
    return "en"


@dataclass(frozen=True)
class StartPayload:
    referrer_id: int | None = None
    source: str | None = None


def parse_start_payload(args: str | None) -> StartPayload:
    """Разбирает deep-link: /start ref_<user_id> или /start src_<код>."""
    if not args:
        return StartPayload()
    args = args.strip()
    if args.startswith("ref_") and args[4:].isdigit():
        return StartPayload(referrer_id=int(args[4:]))
    if args.startswith("src_") and _SOURCE_RE.match(args[4:]):
        return StartPayload(source=args[4:])
    return StartPayload()


async def register(
    session: AsyncSession,
    tg_user: TgUser,
    settings: Settings,
    payload: StartPayload,
) -> User:
    referrer_id = payload.referrer_id
    if referrer_id is not None and (referrer_id == tg_user.id or await repo.get_user(session, referrer_id) is None):
        referrer_id = None

    user = await repo.add_user(
        session,
        User(
            id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            language=detect_language(tg_user.language_code, settings.default_language),
            timezone=settings.default_timezone,
            daily_card_time=settings.default_daily_card_time,
            source=payload.source or ("referral" if referrer_id else None),
            referrer_id=referrer_id,
        ),
    )
    if referrer_id is not None:
        await repo.add_referral(session, referrer_id=referrer_id, referred_id=user.id)
    await repo.log_event(session, user.id, "start", {"source": user.source, "referrer_id": referrer_id})
    return user


async def touch(session: AsyncSession, tg_user: TgUser) -> User | None:
    """Загружает пользователя и обновляет время активности и username."""
    user = await repo.get_user(session, tg_user.id)
    if user is None:
        return None
    user.last_active_at = datetime.now(timezone.utc)
    if user.username != tg_user.username:
        user.username = tg_user.username
    if user.first_name != tg_user.first_name:
        user.first_name = tg_user.first_name
    return user


def set_birth_date(user: User, birth_date: date) -> None:
    user.birth_date = birth_date
    user.zodiac_sign = zodiac_sign(birth_date).value
    user.life_path_number = life_path_number(birth_date)


async def complete_onboarding(
    session: AsyncSession,
    user: User,
    name: str,
    birth_date: date,
    birth_time: time | None,
    birth_city: str | None,
) -> None:
    user.name = name
    user.birth_time = birth_time
    user.birth_city = birth_city
    set_birth_date(user, birth_date)
    await repo.log_event(
        session,
        user.id,
        "profile_completed",
        {"has_birth_time": birth_time is not None, "has_birth_city": birth_city is not None},
    )


async def delete(session: AsyncSession, user: User) -> None:
    await repo.delete_user(session, user.id)
