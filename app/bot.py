import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings, get_settings
from app.db.base import create_engine, create_sessionmaker
from app.handlers import setup_routers
from app.i18n import I18n
from app.middlewares import ContextMiddleware
from app.services.card_images import CardImages
from app.services.horoscope import HoroscopeService
from app.services.limits import Limiter
from app.services.llm import LLM
from app.services.readings import ReadingService

logger = logging.getLogger(__name__)

COMMANDS = ("start", "menu", "profile", "language", "delete_me")


async def setup_bot_profile(bot: Bot, i18n: I18n, settings: Settings) -> None:
    """Команды, имя и описание бота. Имя одно — на русском — для всех языков."""
    try:
        if (await bot.get_my_name()).name != settings.bot_name:
            await bot.set_my_name(name=settings.bot_name)
        for locale in i18n.locales:
            t = i18n.translator(locale)
            # Русский — язык по умолчанию, для остальных языков — английский.
            language_code = None if locale == "en" else locale
            commands = [BotCommand(command=c, description=t(f"cmd-{c.replace('_', '-')}")) for c in COMMANDS]
            await bot.set_my_commands(commands, language_code=language_code)
            await bot.set_my_description(t("bot-description"), language_code=language_code)
            await bot.set_my_short_description(t("bot-short-description"), language_code=language_code)
    except TelegramAPIError:
        # Telegram жёстко ограничивает частоту этих вызовов; бот работает и без них.
        logger.warning("Could not update bot profile", exc_info=True)


def build_dispatcher(
    settings: Settings,
    storage: BaseStorage,
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    bot_id: int,
) -> tuple[Dispatcher, I18n]:
    i18n = I18n(default_locale=settings.default_language, global_args={"bot_name": settings.bot_name})
    llm = LLM(settings, redis)
    dp = Dispatcher(
        storage=storage,
        settings=settings,
        llm=llm,
        limiter=Limiter(redis),
        readings=ReadingService(settings, llm),
        horoscopes=HoroscopeService(llm, redis),
        card_images=CardImages(redis, bot_id),
    )
    dp.update.outer_middleware(ContextMiddleware(sessionmaker, i18n, settings))
    dp.include_router(setup_routers())
    return dp, i18n


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    bot = Bot(settings.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    engine = create_engine(settings.database_url)
    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis)
    dp, i18n = build_dispatcher(settings, storage, create_sessionmaker(engine), redis, bot.id)
    if not settings.anthropic_api_key.get_secret_value():
        logger.info("ANTHROPIC_API_KEY is not set: readings use built-in texts")

    async def on_shutdown() -> None:
        await engine.dispose()
        await storage.close()

    dp.shutdown.register(on_shutdown)
    await setup_bot_profile(bot, i18n, settings)

    if settings.run_mode == "polling":
        await bot.delete_webhook()
        logger.info("Starting in polling mode")
        await dp.start_polling(bot)
        return

    secret = settings.webhook_secret.get_secret_value() or None
    await bot.set_webhook(
        settings.webhook_base_url.rstrip("/") + settings.webhook_path,
        secret_token=secret,
        allowed_updates=dp.resolve_used_update_types(),
    )
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=secret).register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, settings.web_host, settings.web_port).start()
    logger.info("Webhook server listening on %s:%s", settings.web_host, settings.web_port)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
