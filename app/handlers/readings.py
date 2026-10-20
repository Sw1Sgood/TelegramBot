import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import repo
from app.db.models import Reading, User
from app.filters import not_command
from app.i18n import Translator
from app.keyboards import DiaryCb, MenuCb, after_reading_keyboard, cancel_keyboard, diary_keyboard
from app.services import tarot
from app.services.access import is_premium
from app.services.card_images import CardImages
from app.services.limits import Limiter, local_today
from app.services.llm import LLM
from app.services.readings import ReadingService, card_label
from app.services.safety import is_crisis
from app.services.tarot import DrawnCard
from app.states import ReadingFlow

logger = logging.getLogger(__name__)
router = Router(name="readings")

DIARY_SIZE = 10


async def send_cards(bot: Bot, chat_id: int, cards: list[DrawnCard], t: Translator, images: CardImages) -> None:
    media = []
    for drawn in cards:
        source = await images.media(drawn)
        if source is None:
            return  # картинок нет — отправим только текст
        media.append(InputMediaPhoto(media=source, caption=card_label(t, drawn)))
    try:
        if len(media) == 1:
            sent = [await bot.send_photo(chat_id, media[0].media, caption=media[0].caption)]
        else:
            sent = await bot.send_media_group(chat_id, media)
    except Exception:  # картинки — украшение, расклад не должен из-за них сломаться
        logger.warning("Could not send card images", exc_info=True)
        return
    for drawn, message in zip(cards, sent):
        if message.photo:
            await images.remember(drawn, message.photo[-1].file_id)


async def send_reading(
    bot: Bot, chat_id: int, reading: Reading, text: str, t: Translator, images: CardImages
) -> None:
    await send_cards(bot, chat_id, tarot.from_json(reading.cards), t, images)
    await bot.send_message(chat_id, text, reply_markup=after_reading_keyboard(t))


async def deliver_daily_card(
    bot: Bot,
    chat_id: int,
    session: AsyncSession,
    user: User,
    t: Translator,
    settings: Settings,
    readings: ReadingService,
    images: CardImages,
) -> None:
    today = local_today(user.timezone)
    existing = await readings.todays_daily_card(session, user, today)
    if existing is not None:
        await bot.send_message(chat_id, t("daily-card-again"))
        await send_reading(bot, chat_id, existing, existing.response_text or "", t, images)
        return
    shuffling = await bot.send_message(chat_id, t("shuffling"))
    async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
        result = await readings.daily_card(session, user, t, today, await is_premium(session, user, settings))
    await _delete_quietly(bot, shuffling)
    await send_reading(bot, chat_id, result.reading, result.text, t, images)


@router.callback_query(MenuCb.filter(F.section == "daily-card"))
async def menu_daily_card(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    settings: Settings,
    readings: ReadingService,
    card_images: CardImages,
) -> None:
    await state.clear()
    if user is None or not user.is_onboarded:
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    await deliver_daily_card(bot, callback.message.chat.id, session, user, t, settings, readings, card_images)


@router.callback_query(MenuCb.filter(F.section == "question"))
async def menu_question(
    callback: CallbackQuery, state: FSMContext, user: User | None, t: Translator, settings: Settings
) -> None:
    if user is None or not user.is_onboarded:
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    await state.set_state(ReadingFlow.question)
    await callback.message.answer(
        t("question-ask", max=str(settings.question_max_length)), reply_markup=cancel_keyboard(t)
    )


@router.callback_query(ReadingFlow.question, MenuCb.filter(F.section == "cancel"))
async def question_cancel(callback: CallbackQuery, state: FSMContext, t: Translator) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(t("edit-cancelled"))


@router.message(ReadingFlow.question, F.text, not_command)
async def question_text(
    message: Message,
    bot: Bot,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    settings: Settings,
    readings: ReadingService,
    limiter: Limiter,
    llm: LLM,
    card_images: CardImages,
) -> None:
    if user is None or not user.is_onboarded:
        await state.clear()
        await message.answer(t("need-onboarding"))
        return
    question = " ".join(message.text.split())
    if len(question) > settings.question_max_length:
        await message.answer(t("question-too-long", max=str(settings.question_max_length)))
        return
    if is_crisis(question):
        await state.clear()
        await repo.log_event(session, user.id, "crisis_detected")
        await message.answer(t("crisis-response"))
        return
    if await limiter.hit_rate_limit(user.id, settings.llm_rate_limit_seconds):
        await message.answer(t("rate-limited"))
        return

    premium = await is_premium(session, user, settings)
    limit = settings.premium_readings_per_day if premium else settings.free_questions_per_day
    if not await limiter.try_consume(user.id, "question", limit, user.timezone):
        await state.clear()
        await repo.log_event(session, user.id, "paywall_shown", {"reason": "question_limit"})
        await message.answer(t("limit-premium" if premium else "limit-question-free"), reply_markup=after_reading_keyboard(t, new=False))
        return

    await state.clear()
    if llm.is_busy:
        await message.answer(t("queue-notice"))
    shuffling = await message.answer(t("shuffling"))
    try:
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            result = await readings.question(session, user, t, question, local_today(user.timezone), premium)
    except Exception:
        logger.exception("Reading failed")
        await limiter.refund(user.id, "question", user.timezone)
        await _delete_quietly(bot, shuffling)
        await message.answer(t("reading-error"))
        return
    await _delete_quietly(bot, shuffling)
    await send_reading(bot, message.chat.id, result.reading, result.text, t, card_images)
    if not premium:
        await repo.log_event(session, user.id, "paywall_shown", {"reason": "after_free_reading"})
        await message.answer(t("paywall-teaser"))


@router.message(ReadingFlow.question, not_command)
async def question_non_text(message: Message, t: Translator) -> None:
    await message.answer(t("error-text-expected"))


@router.callback_query(MenuCb.filter(F.section == "diary"))
async def menu_diary(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User | None, t: Translator
) -> None:
    await state.clear()
    if user is None or not user.is_onboarded:
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    items = await repo.recent_readings(session, user.id, DIARY_SIZE)
    if not items:
        await callback.message.answer(t("diary-empty"), reply_markup=after_reading_keyboard(t))
        return
    await callback.message.answer(t("diary-title"), reply_markup=diary_keyboard(t, items))


@router.callback_query(DiaryCb.filter())
async def diary_open(
    callback: CallbackQuery,
    callback_data: DiaryCb,
    bot: Bot,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    card_images: CardImages,
) -> None:
    await callback.answer()
    if user is None:
        return
    reading = await repo.get_reading(session, user.id, callback_data.reading_id)
    if reading is None:
        return
    await send_reading(bot, callback.message.chat.id, reading, reading.response_text or "", t, card_images)


async def _delete_quietly(bot: Bot, message: Message) -> None:
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception:  # сообщение могли уже удалить — это не важно
        pass
