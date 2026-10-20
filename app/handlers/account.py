from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.i18n import I18n, Translator
from app.keyboards import DeleteCb, LangCb, delete_confirm_keyboard, language_keyboard, main_menu
from app.services import users

router = Router(name="account")


@router.message(Command("language"))
async def cmd_language(message: Message, state: FSMContext, t: Translator) -> None:
    await state.clear()
    await message.answer(t("choose-language"), reply_markup=language_keyboard())


@router.callback_query(LangCb.filter())
async def set_language(callback: CallbackQuery, callback_data: LangCb, user: User | None, i18n: I18n) -> None:
    await callback.answer()
    if user is None or callback_data.code not in users.SUPPORTED_LANGUAGES:
        return
    user.language = callback_data.code
    t = i18n.translator(user.language)
    await callback.message.edit_text(t("language-changed"))
    if user.is_onboarded:
        await callback.message.answer(t("main-menu-title"), reply_markup=main_menu(t))
    else:
        await callback.message.answer(t("need-onboarding"))


@router.message(Command("delete_me"))
async def cmd_delete_me(message: Message, state: FSMContext, user: User | None, t: Translator) -> None:
    await state.clear()
    if user is None:
        await message.answer(t("delete-done"))
        return
    await message.answer(t("delete-confirm"), reply_markup=delete_confirm_keyboard(t))


@router.callback_query(DeleteCb.filter())
async def delete_confirmed(
    callback: CallbackQuery,
    callback_data: DeleteCb,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    t: Translator,
) -> None:
    await callback.answer()
    if not callback_data.confirm:
        await callback.message.edit_text(t("delete-cancelled"))
        return
    await state.clear()
    if user is not None:
        await users.delete(session, user)
    await callback.message.edit_text(t("delete-done"))
