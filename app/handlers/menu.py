from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.models import User
from app.i18n import Translator
from app.keyboards import MENU_SECTIONS, MenuCb, language_keyboard, main_menu, profile_keyboard
from app.views import profile_text

router = Router(name="menu")


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, user: User | None, t: Translator) -> None:
    await state.clear()
    if user is None or not user.is_onboarded:
        await message.answer(t("need-onboarding"))
        return
    await message.answer(t("main-menu-title"), reply_markup=main_menu(t))


@router.callback_query(MenuCb.filter(F.section == "main"))
async def menu_main(callback: CallbackQuery, state: FSMContext, t: Translator) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(t("main-menu-title"), reply_markup=main_menu(t))


@router.callback_query(MenuCb.filter(F.section == "main-new"))
async def menu_main_new(callback: CallbackQuery, state: FSMContext, t: Translator) -> None:
    # Меню новым сообщением — чтобы не затирать текст расклада.
    await state.clear()
    await callback.answer()
    await callback.message.answer(t("main-menu-title"), reply_markup=main_menu(t))


@router.callback_query(MenuCb.filter(F.section == "profile"))
async def menu_profile(callback: CallbackQuery, state: FSMContext, user: User | None, t: Translator) -> None:
    await state.clear()
    if user is None or not user.is_onboarded:
        await callback.answer(t("need-onboarding"), show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(profile_text(t, user), reply_markup=profile_keyboard(t, user))


@router.callback_query(MenuCb.filter(F.section == "language"))
async def menu_language(callback: CallbackQuery, t: Translator) -> None:
    await callback.answer()
    await callback.message.answer(t("choose-language"), reply_markup=language_keyboard())


@router.callback_query(MenuCb.filter(F.section.in_(MENU_SECTIONS)))
async def menu_coming_soon(callback: CallbackQuery, t: Translator) -> None:
    # Разделы, которые появятся на следующих этапах.
    await callback.answer(t("coming-soon"), show_alert=True)
