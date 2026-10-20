"""Совместимость, нумерология, толкование снов и приглашение друзей."""

import logging
from datetime import date
from html import escape

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import repo
from app.db.models import User
from app.filters import not_command
from app.handlers.readings import after_reading, charge, delete_quietly, deny, refund
from app.i18n import I18n, Translator
from app.keyboards import (
    MenuCb,
    after_reading_keyboard,
    cancel_keyboard,
    invite_keyboard,
    locked_keyboard,
    numerology_keyboard,
)
from app.services import compatibility, numerology
from app.services.access import is_premium
from app.services.astrology import ZODIAC_EMOJI, ZodiacSign
from app.services.dreams import find_symbols
from app.services.limits import Limiter, local_today
from app.services.llm import LLM, LLMUnavailable
from app.services.profile_input import InputError, parse_birth_date
from app.services.readings import ReadingService, load_prompt
from app.services.referrals import FRIEND_READING_BONUS, referral_link
from app.services.safety import is_crisis
from app.states import InsightFlow

logger = logging.getLogger(__name__)
router = Router(name="insights")

DREAM_MAX_LENGTH = 1500


async def _has_paid_access(session: AsyncSession, user: User, settings: Settings) -> bool:
    return await is_premium(session, user, settings) or await repo.get_credits(session, user.id) > 0


def _onboarded(user: User | None) -> bool:
    return user is not None and user.is_onboarded


async def _ai_text(llm: LLM, t: Translator, prompt_name: str, prompt: str, today: date, premium: bool):  # type: ignore[no-untyped-def]
    if not llm.enabled or (not premium and await llm.over_budget(today)):
        return None
    try:
        return await llm.generate(load_prompt(t.locale, prompt_name), prompt, today)
    except LLMUnavailable:
        return None


# --- Совместимость -----------------------------------------------------------------------------


def _sign_text(t: Translator, sign: ZodiacSign) -> str:
    return f"{ZODIAC_EMOJI[sign]} {t(f'zodiac-{sign.value}')}"


def compatibility_template(t: Translator, result: compatibility.Compatibility) -> str:
    hearts = "❤️" * round(result.score / 20) + "🤍" * (5 - round(result.score / 20))
    level = "high" if result.score >= 75 else "mid" if result.score >= 55 else "low"
    return "\n\n".join(
        [
            f"<b>{t('compat-title')}</b>",
            t("compat-people", you=_sign_text(t, result.sign_a), you_lp=str(result.life_path_a),
              partner=_sign_text(t, result.sign_b), partner_lp=str(result.life_path_b)),
            f"<b>{t('compat-score', score=str(result.score))}</b> {hearts}",
            f"<b>{t('compat-elements-label')}</b> {t('compat-pair-' + result.element_pair)}",
            f"<b>{t('compat-numbers-label')}</b> "
            + t("compat-numbers-harmonious" if result.numbers_harmonious else "compat-numbers-different"),
            f"<b>{t('advice-label')}</b> {t('compat-advice-' + level)}",
        ]
    )


@router.callback_query(MenuCb.filter(F.section == "compatibility"))
async def menu_compatibility(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User | None, t: Translator, settings: Settings
) -> None:
    await state.clear()
    if not _onboarded(user):
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    if not await _has_paid_access(session, user, settings):
        await deny(callback.message, session, user, t, "premium-locked-credit")
        return
    await state.set_state(InsightFlow.partner_date)
    await callback.message.answer(t("compat-ask"), reply_markup=cancel_keyboard(t))


@router.message(InsightFlow.partner_date, F.text, not_command)
async def compatibility_date(
    message: Message,
    bot: Bot,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    i18n: I18n,
    settings: Settings,
    limiter: Limiter,
    llm: LLM,
    readings: ReadingService,
) -> None:
    if not _onboarded(user):
        await state.clear()
        return
    today = local_today(user.timezone)
    try:
        partner_birth = parse_birth_date(message.text, today=today)
    except InputError as error:
        await message.answer(t(error.code))
        return
    spent = await charge(session, user, settings, limiter, paid_feature=True)
    await state.clear()
    if isinstance(spent, str):
        await deny(message, session, user, t, spent)
        return

    result = compatibility.calculate(user.birth_date, partner_birth)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        ai = await _ai_text(
            llm, t, "compatibility",
            t("llm-compat-task", you=t(f"zodiac-{result.sign_a.value}"), you_lp=str(result.life_path_a),
              partner=t(f"zodiac-{result.sign_b.value}"), partner_lp=str(result.life_path_b),
              score=str(result.score), name=user.name or "—"),
            today, spent.premium,
        )
    if ai is not None:
        text = "\n\n".join([
            f"<b>{t('compat-title')}</b>",
            t("compat-people", you=_sign_text(t, result.sign_a), you_lp=str(result.life_path_a),
              partner=_sign_text(t, result.sign_b), partner_lp=str(result.life_path_b)),
            f"<b>{t('compat-score', score=str(result.score))}</b>",
            escape(ai.text),
        ])
        reading = await readings.save_text_reading(
            session, user, "compatibility", partner_birth.strftime("%d.%m.%Y"), text, ai.tokens_in, ai.tokens_out, ai.cost_usd
        )
    else:
        text = compatibility_template(t, result)
        reading = await readings.save_text_reading(session, user, "compatibility", partner_birth.strftime("%d.%m.%Y"), text)
    await message.answer(reading.response_text, reply_markup=after_reading_keyboard(t, new=False))
    await after_reading(bot, session, user, i18n, message, t, spent)


# --- Нумерология -------------------------------------------------------------------------------


def numerology_text(t: Translator, user: User, today: date, full: bool) -> str:
    birth = user.birth_date
    life_path = numerology.life_path_number(birth)
    year_number = numerology.personal_year(birth, today.year)
    parts = [
        f"<b>{t('num-title', name=escape(user.name or ''))}</b>",
        f"<b>{t('num-life-path', number=str(life_path))}</b>\n{t(f'lifepath-{life_path}')}",
        f"<b>{t('num-birthday', number=str(numerology.birthday_number(birth)))}</b>\n"
        f"{t('lifepath-' + str(numerology.birthday_number(birth)))}",
        f"<b>{t('num-personal-year', year=str(today.year), number=str(year_number))}</b>\n"
        f"{t('num-year-prefix')} {t(f'personal-{year_number}')}",
    ]
    if full and user.name and numerology.has_letters(user.name):
        for key, number in (
            ("num-expression", numerology.expression_number(user.name)),
            ("num-soul", numerology.soul_number(user.name)),
            ("num-personality", numerology.personality_number(user.name)),
        ):
            parts.append(f"<b>{t(key, number=str(number))}</b>\n{t(f'lifepath-{number}')}")
    elif not full:
        parts.append(t("num-full-teaser"))
    return "\n\n".join(parts)


@router.callback_query(MenuCb.filter(F.section == "numerology"))
async def menu_numerology(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User | None, t: Translator, settings: Settings
) -> None:
    await state.clear()
    if not _onboarded(user):
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    premium = await is_premium(session, user, settings)
    await repo.log_event(session, user.id, "numerology", {"full": premium})
    await callback.message.answer(
        numerology_text(t, user, local_today(user.timezone), full=premium),
        reply_markup=after_reading_keyboard(t, new=False) if premium else numerology_keyboard(t),
    )


@router.callback_query(MenuCb.filter(F.section == "numerology-full"))
async def numerology_full(
    callback: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    i18n: I18n,
    settings: Settings,
    limiter: Limiter,
) -> None:
    if not _onboarded(user):
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    spent = await charge(session, user, settings, limiter, paid_feature=True)
    if isinstance(spent, str):
        await deny(callback.message, session, user, t, spent)
        return
    await callback.message.answer(
        numerology_text(t, user, local_today(user.timezone), full=True), reply_markup=after_reading_keyboard(t, new=False)
    )
    if spent.via == "credit":
        await callback.message.answer(t("credit-spent", left=str(await repo.get_credits(session, user.id))))


# --- Толкование снов ---------------------------------------------------------------------------


def dream_template(t: Translator, dream: str) -> str:
    symbols = find_symbols(dream, t.locale)
    parts = [f"<b>{t('dream-title')}</b>\n<i>«{escape(dream[:200])}{'…' if len(dream) > 200 else ''}»</i>"]
    if symbols:
        parts.append(t("dream-intro"))
        parts.extend(f"<b>{escape(entry['symbol'])}</b>\n{escape(entry['meaning'])}" for entry in symbols)
    else:
        parts.append(t("dream-generic"))
    parts.append(f"<b>{t('advice-label')}</b> {t('dream-advice')}")
    return "\n\n".join(parts)


@router.callback_query(MenuCb.filter(F.section == "dreams"))
async def menu_dreams(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User | None, t: Translator, settings: Settings
) -> None:
    await state.clear()
    if not _onboarded(user):
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    if not await _has_paid_access(session, user, settings):
        await deny(callback.message, session, user, t, "premium-locked-credit")
        return
    await state.set_state(InsightFlow.dream)
    await callback.message.answer(t("dream-ask", max=str(DREAM_MAX_LENGTH)), reply_markup=cancel_keyboard(t))


@router.message(InsightFlow.dream, F.text, not_command)
async def dream_text(
    message: Message,
    bot: Bot,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    i18n: I18n,
    settings: Settings,
    limiter: Limiter,
    llm: LLM,
    readings: ReadingService,
) -> None:
    if not _onboarded(user):
        await state.clear()
        return
    dream = " ".join(message.text.split())
    if len(dream) > DREAM_MAX_LENGTH:
        await message.answer(t("dream-too-long", max=str(DREAM_MAX_LENGTH)))
        return
    if is_crisis(dream):
        await state.clear()
        await repo.log_event(session, user.id, "crisis_detected")
        await message.answer(t("crisis-response"))
        return
    if await limiter.hit_rate_limit(user.id, settings.llm_rate_limit_seconds):
        await message.answer(t("rate-limited"))
        return
    spent = await charge(session, user, settings, limiter, paid_feature=True)
    await state.clear()
    if isinstance(spent, str):
        await deny(message, session, user, t, spent)
        return

    today = local_today(user.timezone)
    thinking = await message.answer(t("dream-thinking"))
    try:
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            ai = await _ai_text(llm, t, "dreams", t("llm-dream-task", name=user.name or "—", dream=dream), today, spent.premium)
        if ai is not None:
            header = dream_template(t, dream).split("\n\n", 1)[0]
            text = f"{header}\n\n{escape(ai.text)}"
            reading = await readings.save_text_reading(session, user, "dream", dream, text, ai.tokens_in, ai.tokens_out, ai.cost_usd)
        else:
            reading = await readings.save_text_reading(session, user, "dream", dream, dream_template(t, dream))
    except Exception:
        logger.exception("Dream reading failed")
        await refund(session, user, limiter, spent)
        await delete_quietly(bot, thinking)
        await message.answer(t("reading-error"))
        return
    await delete_quietly(bot, thinking)
    await message.answer(reading.response_text, reply_markup=after_reading_keyboard(t, new=False))
    await after_reading(bot, session, user, i18n, message, t, spent)


@router.message(InsightFlow.dream, not_command)
async def dream_non_text(message: Message, t: Translator) -> None:
    await message.answer(t("dream-text-only"))


@router.message(InsightFlow.partner_date, not_command)
async def partner_non_text(message: Message, t: Translator) -> None:
    await message.answer(t("error-text-expected"))


# --- Пригласить друга --------------------------------------------------------------------------


@router.callback_query(MenuCb.filter(F.section == "invite"))
async def menu_invite(
    callback: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession, user: User | None, t: Translator, settings: Settings
) -> None:
    await state.clear()
    if not _onboarded(user):
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    username = (await bot.me()).username or ""
    link = referral_link(username, user.id)
    invited, rewarded = await repo.referral_stats(session, user.id)
    await callback.message.answer(
        t("invite-text", link=link, bonus=str(FRIEND_READING_BONUS), invited=str(invited), rewarded=str(rewarded),
          credits=str(await repo.get_credits(session, user.id))),
        reply_markup=invite_keyboard(t, link),
        disable_web_page_preview=True,
    )
