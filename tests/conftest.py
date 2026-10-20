import os
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timezone
from itertools import count
from typing import Any

import pytest
from aiogram import Bot, Router
from aiogram.client.session.base import BaseSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import GetMe, SendMediaGroup, SendMessage, SendPhoto, TelegramMethod
from aiogram.types import CallbackQuery, Chat, Message, PhotoSize, Update, User as TgUser
from fakeredis.aioredis import FakeRedis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.bot import build_dispatcher
from app.config import Settings
from app.db.base import create_engine, create_sessionmaker
from app.db.models import Base


class RecordingSession(BaseSession):
    """Сессия бота без сети: запоминает все запросы к Telegram API."""

    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod[Any]] = []
        self._ids = count(1000)

    async def make_request(self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None) -> Any:
        self.requests.append(method)
        if isinstance(method, GetMe):
            return TgUser(id=42, is_bot=True, first_name="Bot", username="test_bot")
        if isinstance(method, SendMessage):
            return self._message(method.chat_id, text=method.text)
        if isinstance(method, SendPhoto):
            return self._message(method.chat_id, photo=[self._photo()])
        if isinstance(method, SendMediaGroup):
            return [self._message(method.chat_id, photo=[self._photo()]) for _ in method.media]
        return True

    def _message(self, chat_id: int | str, **kwargs: Any) -> Message:
        return Message(
            message_id=next(self._ids),
            date=datetime.now(timezone.utc),
            chat=Chat(id=int(chat_id), type="private"),
            **kwargs,
        )

    def _photo(self) -> PhotoSize:
        n = next(self._ids)
        return PhotoSize(file_id=f"photo-{n}", file_unique_id=f"u-{n}", width=500, height=860)

    def of_type(self, name: str) -> list[TelegramMethod[Any]]:
        return [request for request in self.requests if type(request).__name__ == name]

    async def close(self) -> None:
        pass

    async def stream_content(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError

    def sent_texts(self) -> list[str]:
        return [request.text for request in self.requests if isinstance(request, SendMessage)]

    def clear(self) -> None:
        self.requests.clear()


@pytest.fixture
async def engine(tmp_path) -> AsyncIterator[AsyncEngine]:  # type: ignore[no-untyped-def]
    url = os.environ.get("TEST_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    engine = create_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_sessionmaker(engine)


@pytest.fixture
def settings() -> Settings:
    return Settings(bot_token="42:TEST", _env_file=None)  # type: ignore[call-arg]


class BotHarness:
    """Отправляет боту сообщения и нажатия кнопок от имени пользователя."""

    def __init__(self, settings: Settings, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.session = RecordingSession()
        self.bot = Bot("42:TEST", session=self.session)
        self.redis = FakeRedis()
        self.dp, _ = build_dispatcher(settings, MemoryStorage(), sessionmaker, self.redis, self.bot.id)
        self._update_ids = count(1)
        self._message_ids = count(1)

    def _user(self, user_id: int, first_name: str, language_code: str) -> TgUser:
        return TgUser(id=user_id, is_bot=False, first_name=first_name, language_code=language_code)

    async def send(self, text: str, user_id: int = 1, first_name: str = "Анна", language_code: str = "ru") -> list[str]:
        self.session.clear()
        message = Message(
            message_id=next(self._message_ids),
            date=datetime.now(timezone.utc),
            chat=Chat(id=user_id, type="private"),
            from_user=self._user(user_id, first_name, language_code),
            text=text,
        )
        await self.dp.feed_update(self.bot, Update(update_id=next(self._update_ids), message=message))
        return self.session.sent_texts()

    async def press(self, data: str, user_id: int = 1, first_name: str = "Анна", language_code: str = "ru") -> list[str]:
        self.session.clear()
        message = Message(
            message_id=next(self._message_ids),
            date=datetime.now(timezone.utc),
            chat=Chat(id=user_id, type="private"),
            text="button host",
        )
        callback = CallbackQuery(
            id=str(next(self._update_ids)),
            from_user=self._user(user_id, first_name, language_code),
            chat_instance="test",
            data=data,
            message=message,
        )
        await self.dp.feed_update(self.bot, Update(update_id=next(self._update_ids), callback_query=callback))
        return self.session.sent_texts()

    def edited_texts(self) -> list[str]:
        return [r.text for r in self.session.requests if type(r).__name__ == "EditMessageText"]


def _detach_routers(router: Router) -> None:
    # Роутеры хэндлеров — модульные синглтоны, а каждый тест собирает новый диспетчер.
    for child in list(router.sub_routers):
        _detach_routers(child)
        child._parent_router = None
    router.sub_routers.clear()


@pytest.fixture
def harness(settings: Settings, sessionmaker: async_sessionmaker[AsyncSession]) -> Iterator[BotHarness]:
    harness = BotHarness(settings, sessionmaker)
    yield harness
    _detach_routers(harness.dp)
