from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.i18n import I18n
from app.services import users


class ContextMiddleware(BaseMiddleware):
    """Открывает сессию БД на апдейт, подгружает пользователя и переводчик.

    В хэндлеры попадают: session, user (None, если пользователя ещё нет), t, i18n.
    Сессия коммитится после успешной обработки апдейта.
    """

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession], i18n: I18n, settings: Settings) -> None:
        self.sessionmaker = sessionmaker
        self.i18n = i18n
        self.settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        async with self.sessionmaker() as session:
            user = await users.touch(session, tg_user) if tg_user else None
            if user is not None and user.is_blocked:
                await session.commit()
                return None

            if user is not None:
                language = user.language
            else:
                language = users.detect_language(tg_user.language_code if tg_user else None, self.settings.default_language)

            data["session"] = session
            data["user"] = user
            data["i18n"] = self.i18n
            data["t"] = self.i18n.translator(language)
            result = await handler(event, data)
            await session.commit()
            return result
