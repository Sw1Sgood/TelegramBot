from datetime import date, datetime, time
from html import escape
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.filters import CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.filters import not_command
from app.handlers.readings import deliver_daily_card
from app.db.models import User
from app.i18n import I18n, Translator
from app.keyboards import LangCb, OnboardingCb, language_keyboard, main_menu, single_button
from app.services import users
from app.services.card_images import CardImages
from app.services.readings import ReadingService
from app.services.profile_input import InputError, parse_birth_date, parse_time, validate_city, validate_name
from app.states import Onboarding
from app.views import profile_ready_text

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    settings: Settings,
) -> None:
    await state.clear()
    if user is None:
        user = await users.register(session, message.from_user, settings, users.parse_start_payload(command.args))

    if user.is_onboarded:
        await message.answer(t("welcome-back", name=escape(user.name or "")))
        await message.answer(t("main-menu-title"), reply_markup=main_menu(t))
        return

    await message.answer(t("start-greeting"))
    await message.answer(t("choose-language"), reply_markup=language_keyboard())
    await state.set_state(Onboarding.language)


@router.callback_query(Onboarding.language, LangCb.filter())
async def onboarding_language(
    callback: CallbackQuery,
    callback_data: LangCb,
    state: FSMContext,
    user: User | None,
    i18n: I18n,
) -> None:
    await callback.answer()
    if user is None or callback_data.code not in users.SUPPORTED_LANGUAGES:
        return
    user.language = callback_data.code
    t = i18n.translator(user.language)
    await callback.message.edit_reply_markup(reply_markup=None)

    markup = None
    if callback.from_user.first_name and _is_valid_name(callback.from_user.first_name):
        markup = single_button(
            t("btn-use-tg-name", name=validate_name(callback.from_user.first_name)),
            OnboardingCb(action="use-tg-name"),
        )
    await callback.message.answer(t("ask-name"), reply_markup=markup)
    await state.set_state(Onboarding.name)


@router.message(Onboarding.language, not_command)
async def onboarding_language_text(message: Message, t: Translator) -> None:
    await message.answer(t("choose-language"), reply_markup=language_keyboard())


@router.callback_query(Onboarding.name, OnboardingCb.filter(F.action == "use-tg-name"))
async def onboarding_use_tg_name(callback: CallbackQuery, state: FSMContext, t: Translator) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await _save_name(callback.message, state, t, validate_name(callback.from_user.first_name or ""))


@router.message(Onboarding.name, F.text, not_command)
async def onboarding_name(message: Message, state: FSMContext, t: Translator) -> None:
    try:
        name = validate_name(message.text)
    except InputError as error:
        await message.answer(t(error.code))
        return
    await _save_name(message, state, t, name)


@router.message(Onboarding.birth_date, F.text, not_command)
async def onboarding_birth_date(message: Message, state: FSMContext, t: Translator, settings: Settings) -> None:
    try:
        birth_date = parse_birth_date(message.text, today=_today(settings))
    except InputError as error:
        await message.answer(t(error.code))
        return
    await state.update_data(birth_date=birth_date.isoformat())
    await message.answer(t("ask-birth-time"), reply_markup=single_button(t("btn-skip"), OnboardingCb(action="skip-time")))
    await state.set_state(Onboarding.birth_time)


@router.message(Onboarding.birth_time, F.text, not_command)
async def onboarding_birth_time(message: Message, state: FSMContext, t: Translator) -> None:
    try:
        birth_time = parse_time(message.text)
    except InputError as error:
        await message.answer(t(error.code))
        return
    await state.update_data(birth_time=birth_time.isoformat())
    await _ask_city(message, state, t)


@router.callback_query(Onboarding.birth_time, OnboardingCb.filter(F.action == "skip-time"))
async def onboarding_skip_time(callback: CallbackQuery, state: FSMContext, t: Translator) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.update_data(birth_time=None)
    await _ask_city(callback.message, state, t)


@router.message(Onboarding.birth_city, F.text, not_command)
async def onboarding_birth_city(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    settings: Settings,
    readings: ReadingService,
    card_images: CardImages,
    bot: Bot,
) -> None:
    try:
        city = validate_city(message.text)
    except InputError as error:
        await message.answer(t(error.code))
        return
    await _finish(message, state, session, user, t, city, settings, readings, card_images, bot)


@router.callback_query(Onboarding.birth_city, OnboardingCb.filter(F.action == "skip-city"))
async def onboarding_skip_city(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    settings: Settings,
    readings: ReadingService,
    card_images: CardImages,
    bot: Bot,
) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await _finish(callback.message, state, session, user, t, None, settings, readings, card_images, bot)


@router.message(StateFilter(Onboarding.name, Onboarding.birth_date, Onboarding.birth_time, Onboarding.birth_city), not_command)
async def onboarding_non_text(message: Message, t: Translator) -> None:
    await message.answer(t("error-text-expected"))


async def _save_name(message: Message, state: FSMContext, t: Translator, name: str) -> None:
    await state.update_data(name=name)
    await message.answer(t("ask-birth-date", name=escape(name)))
    await state.set_state(Onboarding.birth_date)


async def _ask_city(message: Message, state: FSMContext, t: Translator) -> None:
    await message.answer(t("ask-birth-city"), reply_markup=single_button(t("btn-skip"), OnboardingCb(action="skip-city")))
    await state.set_state(Onboarding.birth_city)


async def _finish(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    city: str | None,
    settings: Settings,
    readings: ReadingService,
    card_images: CardImages,
    bot: Bot,
) -> None:
    data = await state.get_data()
    await state.clear()
    if user is None or "name" not in data or "birth_date" not in data:
        # Пользователь удалил данные посреди онбординга или состояние потерялось.
        await message.answer(t("need-onboarding"))
        return

    await users.complete_onboarding(
        session,
        user,
        name=data["name"],
        birth_date=date.fromisoformat(data["birth_date"]),
        birth_time=time.fromisoformat(data["birth_time"]) if data.get("birth_time") else None,
        birth_city=city,
    )
    await message.answer(profile_ready_text(t, user))
    # Первый «вау-момент» — сразу бесплатная Карта дня.
    await message.answer(t("daily-card-gift"))
    await deliver_daily_card(bot, message.chat.id, session, user, t, settings, readings, card_images)


def _is_valid_name(text: str) -> bool:
    try:
        validate_name(text)
    except InputError:
        return False
    return True


def _today(settings: Settings) -> date:
    return datetime.now(ZoneInfo(settings.default_timezone)).date()
