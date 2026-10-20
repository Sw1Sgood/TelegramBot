from aiogram.filters.callback_data import CallbackData
from urllib.parse import quote

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.models import Reading, User
from app.i18n import Translator

LANGUAGE_LABELS = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English"}

MENU_SECTIONS = (
    "daily-card",
    "question",
    "spreads",
    "horoscope",
    "compatibility",
    "numerology",
    "dreams",
    "diary",
    "profile",
    "invite",
)

PROFILE_FIELDS = ("name", "birth-date", "birth-time", "birth-city", "daily-time")
# Поля, которые можно очистить (они необязательные).
CLEARABLE_FIELDS = ("birth-time", "birth-city")


class LangCb(CallbackData, prefix="lang"):
    code: str


class OnboardingCb(CallbackData, prefix="onb"):
    action: str  # use-tg-name / skip-time / skip-city


class MenuCb(CallbackData, prefix="menu"):
    section: str


class ProfileCb(CallbackData, prefix="prof"):
    action: str  # edit / clear / toggle-notif / cancel
    field: str = ""


class DeleteCb(CallbackData, prefix="del"):
    confirm: bool


class DiaryCb(CallbackData, prefix="diary"):
    reading_id: int


class HoroscopeCb(CallbackData, prefix="horo"):
    period: str  # day / week / month


class SpreadCb(CallbackData, prefix="spread"):
    kind: str


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in LANGUAGE_LABELS.items():
        builder.button(text=label, callback_data=LangCb(code=code))
    return builder.as_markup()


def single_button(text: str, callback_data: CallbackData) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback_data.pack())]])


def main_menu(t: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for section in MENU_SECTIONS:
        builder.button(text=t(f"menu-{section}"), callback_data=MenuCb(section=section))
    builder.adjust(2)
    return builder.as_markup()


def profile_keyboard(t: Translator, user: User) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for field in PROFILE_FIELDS:
        builder.button(text=t(f"btn-edit-{field}"), callback_data=ProfileCb(action="edit", field=field))
    builder.button(
        text=t("btn-notif-turn-off" if user.notifications_on else "btn-notif-turn-on"),
        callback_data=ProfileCb(action="toggle-notif"),
    )
    builder.button(text=t("btn-change-language"), callback_data=MenuCb(section="language"))
    builder.button(text=t("btn-back-menu"), callback_data=MenuCb(section="main"))
    builder.adjust(2, 2, 1, 1, 2)
    return builder.as_markup()


def edit_field_keyboard(t: Translator, field: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if field in CLEARABLE_FIELDS:
        builder.button(text=t("btn-clear"), callback_data=ProfileCb(action="clear", field=field))
    builder.button(text=t("btn-cancel"), callback_data=ProfileCb(action="cancel"))
    builder.adjust(1)
    return builder.as_markup()


def delete_confirm_keyboard(t: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn-delete-yes"), callback_data=DeleteCb(confirm=True))
    builder.button(text=t("btn-cancel"), callback_data=DeleteCb(confirm=False))
    builder.adjust(1)
    return builder.as_markup()


def cancel_keyboard(t: Translator) -> InlineKeyboardMarkup:
    return single_button(t("btn-cancel"), MenuCb(section="cancel"))


def after_reading_keyboard(t: Translator, new: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if new:
        builder.button(text=t("btn-new-reading"), callback_data=MenuCb(section="question"))
    builder.button(text=t("btn-back-menu"), callback_data=MenuCb(section="main-new"))
    builder.adjust(1)
    return builder.as_markup()


def horoscope_keyboard(t: Translator, locked: tuple[str, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for period in ("day", "week", "month"):
        label = t(f"btn-horo-{period}")
        builder.button(text=f"{label} 🔒" if period in locked else label, callback_data=HoroscopeCb(period=period))
    builder.button(text=t("btn-back-menu"), callback_data=MenuCb(section="main"))
    builder.adjust(3, 1)
    return builder.as_markup()


DIARY_ICONS = {"daily": "🃏", "question": "🔮", "compatibility": "💞", "dream": "🌙"}


def spreads_keyboard(t: Translator, kinds: tuple[str, ...], locked: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for kind in kinds:
        label = t(f"spread-btn-{kind}")
        builder.button(text=f"{label} 🔒" if locked else label, callback_data=SpreadCb(kind=kind))
    builder.button(text=t("btn-back-menu"), callback_data=MenuCb(section="main"))
    builder.adjust(1)
    return builder.as_markup()


def locked_keyboard(t: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("menu-invite"), callback_data=MenuCb(section="invite"))
    builder.button(text=t("btn-back-menu"), callback_data=MenuCb(section="main-new"))
    builder.adjust(1)
    return builder.as_markup()


def numerology_keyboard(t: Translator) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("num-btn-full"), callback_data=MenuCb(section="numerology-full"))
    builder.button(text=t("btn-back-menu"), callback_data=MenuCb(section="main-new"))
    builder.adjust(1)
    return builder.as_markup()


def invite_keyboard(t: Translator, link: str) -> InlineKeyboardMarkup:
    share_url = f"https://t.me/share/url?url={quote(link)}&text={quote(t('invite-share-text'))}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("invite-btn-share"), url=share_url)],
            [InlineKeyboardButton(text=t("btn-back-menu"), callback_data=MenuCb(section="main-new").pack())],
        ]
    )


def diary_keyboard(t: Translator, readings: list[Reading]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for reading in readings:
        icon = DIARY_ICONS.get(reading.type, "🌟")
        title = reading.question or t("diary-daily-card")
        if len(title) > 40:
            title = title[:39] + "…"
        builder.button(
            text=f"{icon} {reading.created_at:%d.%m} · {title}", callback_data=DiaryCb(reading_id=reading.id)
        )
    builder.button(text=t("btn-back-menu"), callback_data=MenuCb(section="main"))
    builder.adjust(1)
    return builder.as_markup()
