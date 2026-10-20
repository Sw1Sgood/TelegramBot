from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import repo
from app.db.models import User
from app.filters import not_command
from app.i18n import Translator
from app.keyboards import CLEARABLE_FIELDS, PROFILE_FIELDS, ProfileCb, edit_field_keyboard, profile_keyboard
from app.services import users
from app.services.profile_input import InputError, parse_birth_date, parse_time, validate_city, validate_name
from app.states import ProfileEdit
from app.views import profile_text

router = Router(name="profile")


@router.message(Command("profile"))
async def cmd_profile(message: Message, state: FSMContext, user: User | None, t: Translator) -> None:
    await state.clear()
    if user is None or not user.is_onboarded:
        await message.answer(t("need-onboarding"))
        return
    await message.answer(profile_text(t, user), reply_markup=profile_keyboard(t, user))


@router.callback_query(ProfileCb.filter(F.action == "edit"))
async def edit_start(
    callback: CallbackQuery, callback_data: ProfileCb, state: FSMContext, user: User | None, t: Translator
) -> None:
    await callback.answer()
    if user is None or not user.is_onboarded or callback_data.field not in PROFILE_FIELDS:
        return
    await state.set_state(ProfileEdit.value)
    await state.update_data(field=callback_data.field)
    await callback.message.answer(
        t(f"edit-prompt-{callback_data.field}"), reply_markup=edit_field_keyboard(t, callback_data.field)
    )


@router.message(ProfileEdit.value, F.text, not_command)
async def edit_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    settings: Settings,
) -> None:
    field = (await state.get_data()).get("field")
    if user is None or field not in PROFILE_FIELDS:
        await state.clear()
        return
    try:
        _apply(user, field, message.text, settings)
    except InputError as error:
        await message.answer(t(error.code))
        return
    await repo.log_event(session, user.id, "profile_edited", {"field": field})
    await state.clear()
    await message.answer(t("profile-saved"))
    await message.answer(profile_text(t, user), reply_markup=profile_keyboard(t, user))


@router.message(ProfileEdit.value, not_command)
async def edit_value_non_text(message: Message, t: Translator) -> None:
    await message.answer(t("error-text-expected"))


@router.callback_query(ProfileCb.filter(F.action == "clear"))
async def edit_clear(
    callback: CallbackQuery, callback_data: ProfileCb, state: FSMContext, user: User | None, t: Translator
) -> None:
    await state.clear()
    await callback.answer()
    if user is None or not user.is_onboarded or callback_data.field not in CLEARABLE_FIELDS:
        return
    if callback_data.field == "birth-time":
        user.birth_time = None
    else:
        user.birth_city = None
    await callback.message.edit_text(t("profile-saved"))
    await callback.message.answer(profile_text(t, user), reply_markup=profile_keyboard(t, user))


@router.callback_query(ProfileCb.filter(F.action == "cancel"))
async def edit_cancel(callback: CallbackQuery, state: FSMContext, t: Translator) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(t("edit-cancelled"))


@router.callback_query(ProfileCb.filter(F.action == "toggle-notif"))
async def toggle_notifications(callback: CallbackQuery, user: User | None, t: Translator) -> None:
    await callback.answer()
    if user is None or not user.is_onboarded:
        return
    user.notifications_on = not user.notifications_on
    await callback.message.edit_text(profile_text(t, user), reply_markup=profile_keyboard(t, user))


def _apply(user: User, field: str, text: str, settings: Settings) -> None:
    match field:
        case "name":
            user.name = validate_name(text)
        case "birth-date":
            today = datetime.now(ZoneInfo(settings.default_timezone)).date()
            users.set_birth_date(user, parse_birth_date(text, today=today))
        case "birth-time":
            user.birth_time = parse_time(text)
        case "birth-city":
            user.birth_city = validate_city(text)
        case "daily-time":
            user.daily_card_time = parse_time(text)
