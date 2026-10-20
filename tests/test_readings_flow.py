from decimal import Decimal
from unittest.mock import AsyncMock

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Reading
from app.keyboards import DiaryCb, HoroscopeCb, MenuCb
from app.services.llm import LLMResult, LLMUnavailable
from tests.conftest import BotHarness
from tests.test_onboarding_flow import _onboard


async def _readings(sessionmaker: async_sessionmaker[AsyncSession]) -> list[Reading]:
    async with sessionmaker() as session:
        return list((await session.execute(select(Reading).order_by(Reading.id))).scalars())


def _enable_fake_ai(harness: BotHarness, generate: AsyncMock) -> None:
    llm = harness.dp["llm"]
    llm._client = object()  # «ключ есть»
    llm.generate = generate


async def test_onboarding_gives_daily_card_with_image(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await harness.send("/start")
    from app.keyboards import LangCb, OnboardingCb

    await harness.press(LangCb(code="ru").pack())
    await harness.send("Анна")
    await harness.send("25.03.1995")
    await harness.press(OnboardingCb(action="skip-time").pack())
    await harness.press(OnboardingCb(action="skip-city").pack())

    photos = harness.session.of_type("SendPhoto")
    assert len(photos) == 1
    readings = await _readings(sessionmaker)
    assert [r.type for r in readings] == ["daily"]
    # Сообщение «Тасую колоду…» удаляется.
    assert harness.session.of_type("DeleteMessage")


async def test_daily_card_is_once_per_day(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness)
    first = (await _readings(sessionmaker))[0]

    texts = await harness.press(MenuCb(section="daily-card").pack())
    assert texts[0].startswith("Карта дня уже выпала сегодня")
    assert texts[1] == first.response_text
    assert len(await _readings(sessionmaker)) == 1
    # Повторная отправка картинки идёт по file_id из кэша, без загрузки файла.
    assert isinstance(harness.session.of_type("SendPhoto")[0].photo, str)


async def test_question_reading_and_free_limit(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness)
    texts = await harness.press(MenuCb(section="question").pack())
    assert texts[0].startswith("❓ Задай вопрос картам")

    texts = await harness.send("Что мне важно понять о работе?")
    groups = harness.session.of_type("SendMediaGroup")
    assert len(groups) == 1 and len(groups[0].media) == 3
    reading_text = next(text for text in texts if "Расклад на вопрос" in text)
    for position in ("Прошлое — ", "Настоящее — ", "Будущее — ", "Совет:"):
        assert position in reading_text
    assert "«Что мне важно понять о работе?»" in reading_text
    assert texts[-1].startswith("💫 Хочешь разобрать глубже?")

    question = (await _readings(sessionmaker))[-1]
    assert question.type == "question" and len(question.cards) == 3

    # Второй бесплатный расклад за день блокируется.
    await harness.redis.delete("rate:1")
    await harness.press(MenuCb(section="question").pack())
    texts = await harness.send("А что с любовью?")
    assert texts[0].startswith("Бесплатный расклад на сегодня уже сделан")
    assert len(await _readings(sessionmaker)) == 2


async def test_rate_limit(harness: BotHarness, settings) -> None:  # type: ignore[no-untyped-def]
    settings.premium_for_all = True
    await _onboard(harness)
    await harness.press(MenuCb(section="question").pack())
    await harness.send("Первый вопрос?")
    await harness.press(MenuCb(section="question").pack())
    texts = await harness.send("Второй вопрос сразу?")
    assert texts == ["Секунду, карты ещё тасуются… Попробуй через пару секунд."]


async def test_crisis_question_is_not_read(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness)
    await harness.press(MenuCb(section="question").pack())
    texts = await harness.send("Я не хочу жить, что делать?")
    assert "8-800-2000-122" in texts[0]
    assert [r.type for r in await _readings(sessionmaker)] == ["daily"]
    # Лимит не потрачен: обычный вопрос после этого проходит.
    await harness.press(MenuCb(section="question").pack())
    texts = await harness.send("Как мне найти опору?")
    assert any("Расклад на вопрос" in text for text in texts)


async def test_question_too_long(harness: BotHarness) -> None:
    await _onboard(harness)
    await harness.press(MenuCb(section="question").pack())
    texts = await harness.send("а" * 501)
    assert texts[0].startswith("Вопрос получился длинным")


async def test_ai_reading_is_used_and_costed(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness)
    generate = AsyncMock(return_value=LLMResult("Анна, карты говорят <тепло>.", 1500, 400, Decimal("0.00035")))
    _enable_fake_ai(harness, generate)

    await harness.press(MenuCb(section="question").pack())
    texts = await harness.send("Что меня ждёт?")
    reading_text = next(text for text in texts if "Расклад на вопрос" in text)
    assert "Анна, карты говорят &lt;тепло&gt;." in reading_text  # текст ИИ экранируется

    prompt = generate.call_args.args[1]
    assert "Что меня ждёт?" in prompt and "Овен" in prompt and "Карта дня" in prompt  # история раскладов
    reading = (await _readings(sessionmaker))[-1]
    assert (reading.tokens_in, reading.tokens_out, reading.cost_usd) == (1500, 400, Decimal("0.00035"))


async def test_ai_failure_falls_back_to_texts(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness)
    _enable_fake_ai(harness, AsyncMock(side_effect=LLMUnavailable("timeout")))
    await harness.press(MenuCb(section="question").pack())
    texts = await harness.send("Что меня ждёт?")
    reading_text = next(text for text in texts if "Расклад на вопрос" in text)
    assert "Совет:" in reading_text and "Прошлое — " in reading_text


async def test_horoscope_today_free_week_locked(harness: BotHarness, settings) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness)
    texts = await harness.press(MenuCb(section="horoscope").pack())
    assert "Гороскоп для знака <b>Овен</b>" in texts[0]

    texts = await harness.press(HoroscopeCb(period="day").pack())
    assert "Овен — гороскоп на сегодня" in texts[0]
    assert "личное число дня" in texts[0]

    harness.session.clear()
    await harness.press(HoroscopeCb(period="week").pack())
    answers = harness.session.of_type("AnswerCallbackQuery")
    assert answers[0].text.startswith("🔒")

    settings.premium_for_all = True
    texts = await harness.press(HoroscopeCb(period="month").pack())
    assert "гороскоп на " in texts[0] and "личное число месяца" in texts[0]


async def test_diary(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness)
    await harness.press(MenuCb(section="question").pack())
    await harness.send("Как пройдёт неделя?")

    texts = await harness.press(MenuCb(section="diary").pack())
    assert texts[0].startswith("📖 Твой дневник")
    markup = harness.session.of_type("SendMessage")[0].reply_markup
    buttons = [row[0].text for row in markup.inline_keyboard]
    assert buttons[0].startswith("🔮") and "Как пройдёт неделя?" in buttons[0]
    assert buttons[1].startswith("🃏")

    question = (await _readings(sessionmaker))[-1]
    texts = await harness.press(DiaryCb(reading_id=question.id).pack())
    assert texts[-1] == question.response_text

    # Чужой расклад открыть нельзя.
    texts = await harness.press(DiaryCb(reading_id=question.id).pack(), user_id=999)
    assert texts == []
