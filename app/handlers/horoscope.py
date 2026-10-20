from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import repo
from app.db.models import User
from app.i18n import Translator
from app.keyboards import HoroscopeCb, MenuCb, after_reading_keyboard, horoscope_keyboard
from app.services.access import is_premium
from app.services.astrology import ZODIAC_EMOJI, ZodiacSign
from app.services.horoscope import PERIODS, HoroscopeService, Period
from app.services.limits import local_today

router = Router(name="horoscope")

# Бесплатно — только гороскоп на сегодня.
FREE_PERIODS = ("day",)


@router.callback_query(MenuCb.filter(F.section == "horoscope"))
async def menu_horoscope(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    settings: Settings,
) -> None:
    await state.clear()
    if user is None or not user.is_onboarded or user.zodiac_sign is None:
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    sign = ZodiacSign(user.zodiac_sign)
    premium = await is_premium(session, user, settings)
    await callback.message.answer(
        t("horo-choose", sign_emoji=ZODIAC_EMOJI[sign], sign=t(f"zodiac-{sign.value}")),
        reply_markup=horoscope_keyboard(t, locked=() if premium else tuple(p for p in PERIODS if p not in FREE_PERIODS)),
    )


@router.callback_query(HoroscopeCb.filter())
async def show_horoscope(
    callback: CallbackQuery,
    callback_data: HoroscopeCb,
    session: AsyncSession,
    user: User | None,
    t: Translator,
    settings: Settings,
    horoscopes: HoroscopeService,
) -> None:
    if user is None or not user.is_onboarded or user.zodiac_sign is None or user.birth_date is None:
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    if callback_data.period not in PERIODS:
        await callback.answer()
        return
    if callback_data.period not in FREE_PERIODS and not await is_premium(session, user, settings):
        await repo.log_event(session, user.id, "paywall_shown", {"reason": f"horoscope_{callback_data.period}"})
        await callback.answer(t("premium-locked"), show_alert=True)
        return
    await callback.answer()
    today = local_today(user.timezone)
    async with ChatActionSender.typing(bot=callback.bot, chat_id=callback.message.chat.id):
        text = await horoscopes.render(
            t, ZodiacSign(user.zodiac_sign), user.birth_date, Period.for_day(callback_data.period, today), today
        )
    await repo.log_event(session, user.id, "horoscope", {"period": callback_data.period})
    await callback.message.answer(text, reply_markup=after_reading_keyboard(t, new=False))
