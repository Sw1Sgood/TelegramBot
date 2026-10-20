"""Сборка текстов, которые показываются в нескольких хэндлерах."""

from html import escape

from app.db.models import User
from app.i18n import Translator
from app.keyboards import LANGUAGE_LABELS
from app.services.astrology import ZODIAC_EMOJI, ZodiacSign

MOSCOW_TZ = "Europe/Moscow"


def format_date(value) -> str:  # type: ignore[no-untyped-def]
    return value.strftime("%d.%m.%Y")


def format_time(value) -> str:  # type: ignore[no-untyped-def]
    return value.strftime("%H:%M")


def sign_parts(t: Translator, user: User) -> tuple[str, str]:
    if user.zodiac_sign is None:
        return "", t("profile-not-set")
    sign = ZodiacSign(user.zodiac_sign)
    return ZODIAC_EMOJI[sign], t(f"zodiac-{sign.value}")


def profile_ready_text(t: Translator, user: User) -> str:
    emoji, sign = sign_parts(t, user)
    return t(
        "profile-ready",
        name=escape(user.name or ""),
        sign_emoji=emoji,
        sign=sign,
        life_path=str(user.life_path_number),
        life_path_description=t(f"lifepath-{user.life_path_number}"),
    )


def profile_text(t: Translator, user: User) -> str:
    not_set = t("profile-not-set")
    emoji, sign = sign_parts(t, user)
    return t(
        "profile-card",
        name=escape(user.name or not_set),
        birth_date=format_date(user.birth_date) if user.birth_date else not_set,
        birth_time=format_time(user.birth_time) if user.birth_time else not_set,
        birth_city=escape(user.birth_city) if user.birth_city else not_set,
        sign_emoji=emoji,
        sign=sign,
        life_path=str(user.life_path_number) if user.life_path_number else not_set,
        language=LANGUAGE_LABELS.get(user.language, user.language),
        timezone=t("profile-tz-moscow") if user.timezone == MOSCOW_TZ else user.timezone,
        daily_time=format_time(user.daily_card_time),
        notifications=t("notif-on" if user.notifications_on else "notif-off"),
        plan=t("plan-free"),
    )
