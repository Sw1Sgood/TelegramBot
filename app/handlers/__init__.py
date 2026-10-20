from aiogram import Router
from aiogram.types import CallbackQuery

from app.handlers import account, menu, profile, start

fallback_router = Router(name="fallback")


@fallback_router.callback_query()
async def stale_callback(callback: CallbackQuery) -> None:
    # Кнопки из старых сообщений: просто убираем «часики».
    await callback.answer()


def setup_routers() -> Router:
    root = Router(name="root")
    # Порядок важен: онбординг и редактирование профиля (FSM) раньше общих хэндлеров,
    # fallback — последним.
    root.include_routers(start.router, profile.router, account.router, menu.router, fallback_router)
    return root
