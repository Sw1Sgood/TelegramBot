import logging
from dataclasses import dataclass

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import repo
from app.db.models import Reading, User
from app.filters import not_command
from app.i18n import I18n, Translator
from app.keyboards import (
    DiaryCb,
    MenuCb,
    SpreadCb,
    after_reading_keyboard,
    cancel_keyboard,
    diary_keyboard,
    locked_keyboard,
    spreads_keyboard,
)
from app.services import tarot
from app.services.access import is_premium
from app.services.card_images import CardImages
from app.services.limits import Limiter, local_today
from app.services.llm import LLM
from app.services.readings import BIG_SPREADS, SPREADS, ReadingService, card_label
from app.services.referrals import FRIEND_READING_BONUS, reward_for_first_reading
from app.services.safety import is_crisis
from app.services.tarot import DrawnCard
from app.states import ReadingFlow

logger = logging.getLogger(__name__)
router = Router(name="readings")

DIARY_SIZE = 10


# --- Доступ: подписка, бесплатный лимит или бонусный расклад -----------------------------------


@dataclass(frozen=True)
class Charge:
    premium: bool
    via: str  # premium / free / credit


async def charge(
    session: AsyncSession, user: User, settings: Settings, limiter: Limiter, paid_feature: bool
) -> Charge | str:
    """Списывает одно использование. Возвращает Charge или ключ текста отказа."""
    if await is_premium(session, user, settings):
        if await limiter.try_consume(user.id, "premium", settings.premium_readings_per_day, user.timezone):
            return Charge(True, "premium")
        return "limit-premium"
    if not paid_feature and await limiter.try_consume(user.id, "question", settings.free_questions_per_day, user.timezone):
        return Charge(False, "free")
    if await repo.consume_credit(session, user.id):
        return Charge(False, "credit")
    return "premium-locked-credit" if paid_feature else "limit-question-free"


async def refund(session: AsyncSession, user: User, limiter: Limiter, spent: Charge) -> None:
    if spent.via == "credit":
        await repo.add_credits(session, user.id, 1)
    else:
        await limiter.refund(user.id, "premium" if spent.via == "premium" else "question", user.timezone)


async def deny(message: Message, session: AsyncSession, user: User, t: Translator, reason: str) -> None:
    await repo.log_event(session, user.id, "paywall_shown", {"reason": reason})
    markup = locked_keyboard(t) if reason != "limit-premium" else after_reading_keyboard(t, new=False)
    await message.answer(t(reason), reply_markup=markup)


async def after_reading(
    bot: Bot, session: AsyncSession, user: User, i18n: I18n, message: Message, t: Translator, spent: Charge
) -> None:
    """Бонус пригласившему и мягкое приглашение к подписке."""
    referrer_id = await reward_for_first_reading(session, user)
    if referrer_id is not None:
        referrer = await repo.get_user(session, referrer_id)
        friend_t = i18n.translator(referrer.language if referrer else None)
        try:
            await bot.send_message(referrer_id, friend_t("referral-rewarded", bonus=str(FRIEND_READING_BONUS)))
        except Exception:  # пригласивший мог заблокировать бота
            logger.info("Could not notify referrer %s", referrer_id)
    if spent.via == "free":
        await repo.log_event(session, user.id, "paywall_shown", {"reason": "after_free_reading"})
        await message.answer(t("paywall-teaser"))
    elif spent.via == "credit":
        await message.answer(t("credit-spent", left=str(await repo.get_credits(session, user.id))))


# --- Отправка ----------------------------------------------------------------------------------


async def send_cards(bot: Bot, chat_id: int, cards: list[DrawnCard], t: Translator, images: CardImages) -> None:
    if not cards:
        return
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
    new = reading.type in SPREADS
    await bot.send_message(chat_id, text, reply_markup=after_reading_keyboard(t, new=new))


async def delete_quietly(bot: Bot, message: Message) -> None:
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception:  # сообщение могли уже удалить — это не важно
        pass


# --- Карта дня ---------------------------------------------------------------------------------


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
    await delete_quietly(bot, shuffling)
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


# --- Расклады на вопрос и большие расклады ----------------------------------------------------


async def _ask_question(callback: CallbackQuery, state: FSMContext, t: Translator, settings: Settings, kind: str) -> None:
    await state.set_state(ReadingFlow.question)
    await state.update_data(spread=kind)
    key = "question-ask" if kind == "question" else f"spread-ask-{kind}"
    await callback.message.answer(t(key, max=str(settings.question_max_length)), reply_markup=cancel_keyboard(t))


@router.callback_query(MenuCb.filter(F.section == "question"))
async def menu_question(
    callback: CallbackQuery, state: FSMContext, user: User | None, t: Translator, settings: Settings
) -> None:
    if user is None or not user.is_onboarded:
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    await _ask_question(callback, state, t, settings, "question")


@router.callback_query(MenuCb.filter(F.section == "spreads"))
async def menu_spreads(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    settings: Settings,
) -> None:
    await state.clear()
    if user is None or not user.is_onboarded:
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    unlocked = await is_premium(session, user, settings) or await repo.get_credits(session, user.id) > 0
    await callback.message.answer(t("spreads-title"), reply_markup=spreads_keyboard(t, BIG_SPREADS, locked=not unlocked))


@router.callback_query(SpreadCb.filter())
async def choose_spread(
    callback: CallbackQuery,
    callback_data: SpreadCb,
    state: FSMContext,
    user: User | None,
    t: Translator,
    settings: Settings,
) -> None:
    if user is None or not user.is_onboarded or callback_data.kind not in BIG_SPREADS:
        await callback.answer()
        return
    await callback.answer()
    # Доступ проверяется после ввода вопроса — тогда же списывается расклад.
    await _ask_question(callback, state, t, settings, callback_data.kind)


@router.callback_query(MenuCb.filter(F.section == "cancel"))
async def flow_cancel(callback: CallbackQuery, state: FSMContext, t: Translator) -> None:
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
    i18n: I18n,
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
    spread = SPREADS.get((await state.get_data()).get("spread", "question"), SPREADS["question"])
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

    spent = await charge(session, user, settings, limiter, paid_feature=spread.premium)
    await state.clear()
    if isinstance(spent, str):
        await deny(message, session, user, t, spent)
        return

    if llm.is_busy:
        await message.answer(t("queue-notice"))
    shuffling = await message.answer(t("shuffling"))
    try:
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            result = await readings.spread(
                session, user, t, spread, question, local_today(user.timezone), spent.premium
            )
    except Exception:
        logger.exception("Reading failed")
        await refund(session, user, limiter, spent)
        await delete_quietly(bot, shuffling)
        await message.answer(t("reading-error"))
        return
    await delete_quietly(bot, shuffling)
    await send_reading(bot, message.chat.id, result.reading, result.text, t, card_images)
    await after_reading(bot, session, user, i18n, message, t, spent)


@router.message(ReadingFlow.question, not_command)
async def question_non_text(message: Message, t: Translator) -> None:
    await message.answer(t("error-text-expected"))


# --- Дневник -----------------------------------------------------------------------------------


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
