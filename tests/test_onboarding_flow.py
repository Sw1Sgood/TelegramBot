from datetime import date, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Event, Referral, User
from app.keyboards import DeleteCb, LangCb, MenuCb, OnboardingCb, ProfileCb
from tests.conftest import BotHarness


async def _get_user(sessionmaker: async_sessionmaker[AsyncSession], user_id: int) -> User | None:
    async with sessionmaker() as session:
        return await session.get(User, user_id)


async def _onboard(harness: BotHarness, user_id: int = 1, start: str = "/start") -> None:
    await harness.send(start, user_id=user_id)
    await harness.press(LangCb(code="ru").pack(), user_id=user_id)
    await harness.send("Анна", user_id=user_id)
    await harness.send("25.03.1995", user_id=user_id)
    await harness.press(OnboardingCb(action="skip-time").pack(), user_id=user_id)
    await harness.press(OnboardingCb(action="skip-city").pack(), user_id=user_id)


async def test_full_onboarding(harness: BotHarness, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    texts = await harness.send("/start src_vk_ads")
    assert "Твой личный астролог" in texts[0]
    assert "для развлечения и самопознания" in texts[0]

    texts = await harness.press(LangCb(code="ru").pack())
    assert texts == ["Как тебя зовут? Напиши имя, которым мне к тебе обращаться."]

    texts = await harness.send("Анна")
    assert "Приятно познакомиться, Анна" in texts[0]

    assert (await harness.send("31.02.1995"))[0].startswith("Такой даты не существует")
    texts = await harness.send("25.03.1995")
    assert "время рождения" in texts[0]

    texts = await harness.send("14:30")
    assert "В каком городе" in texts[0]

    texts = await harness.send("Москва")
    assert "Твой знак зодиака — <b>Овен</b>" in texts[0]
    assert "Число жизненного пути — <b>7</b>" in texts[0]
    assert "первая Карта дня" in texts[1]
    assert texts[2] == "🔮 Тасую колоду…"
    assert "<b>🃏 Карта дня — " in texts[3]
    assert "Совет дня:" in texts[3]

    user = await _get_user(sessionmaker, 1)
    assert user is not None
    assert (user.name, user.birth_date, user.birth_time, user.birth_city) == ("Анна", date(1995, 3, 25), time(14, 30), "Москва")
    assert (user.zodiac_sign, user.life_path_number) == ("aries", 7)
    assert (user.source, user.language, user.timezone) == ("vk_ads", "ru", "Europe/Moscow")

    # Повторный /start — приветствие и меню, без повторного онбординга.
    texts = await harness.send("/start")
    assert texts[0].startswith("С возвращением, Анна")


async def test_optional_fields_can_be_skipped(harness: BotHarness, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    await _onboard(harness)
    user = await _get_user(sessionmaker, 1)
    assert user is not None and user.is_onboarded
    assert user.birth_time is None and user.birth_city is None


async def test_english_onboarding_keeps_russian_bot_name(harness: BotHarness) -> None:
    texts = await harness.send("/start", language_code="en")
    assert "This is «Твой личный астролог | Таро и гороскоп»" in texts[0]
    texts = await harness.press(LangCb(code="en").pack(), language_code="en")
    assert texts[0].startswith("What's your name?")


async def test_commands_are_not_taken_as_answers(harness: BotHarness, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    await harness.send("/start")
    await harness.press(LangCb(code="ru").pack())
    texts = await harness.send("/menu")
    assert texts == ["Сначала давай познакомимся — нажми /start"]
    user = await _get_user(sessionmaker, 1)
    assert user is not None and user.name is None


async def test_use_telegram_name_button(harness: BotHarness, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    await harness.send("/start", first_name="Мария")
    await harness.press(LangCb(code="ru").pack(), first_name="Мария")
    texts = await harness.press(OnboardingCb(action="use-tg-name").pack(), first_name="Мария")
    assert "Приятно познакомиться, Мария" in texts[0]


async def test_referral_is_recorded_once(harness: BotHarness, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    await _onboard(harness, user_id=1)
    await harness.send("/start ref_1", user_id=2)
    await harness.send("/start ref_1", user_id=2)  # повторный переход не создаёт вторую запись
    await harness.send("/start ref_3", user_id=3)  # сам себя пригласить нельзя

    async with sessionmaker() as session:
        referrals = (await session.execute(select(Referral))).scalars().all()
        assert [(r.referrer_id, r.referred_id) for r in referrals] == [(1, 2)]
        invited = await session.get(User, 2)
        assert invited is not None and invited.referrer_id == 1 and invited.source == "referral"
        self_invited = await session.get(User, 3)
        assert self_invited is not None and self_invited.referrer_id is None


async def test_profile_edit_recomputes_sign(harness: BotHarness, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    await _onboard(harness)
    await harness.press(MenuCb(section="profile").pack())
    assert "Твой профиль" in harness.edited_texts()[0]

    await harness.press(ProfileCb(action="edit", field="birth-date").pack())
    assert (await harness.send("не дата"))[0].startswith("Не получилось разобрать дату")
    texts = await harness.send("15.08.1990")
    assert texts[0] == "Сохранено ✅"
    assert "Лев" in texts[1]

    await harness.press(ProfileCb(action="edit", field="daily-time").pack())
    await harness.send("07:45")
    await harness.press(ProfileCb(action="toggle-notif").pack())

    user = await _get_user(sessionmaker, 1)
    assert user is not None
    assert (user.zodiac_sign, user.daily_card_time, user.notifications_on) == ("leo", time(7, 45), False)


async def test_language_switch(harness: BotHarness, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    await _onboard(harness)
    await harness.send("/language")
    texts = await harness.press(LangCb(code="en").pack())
    assert harness.edited_texts() == ["Done, we'll talk in English now 🇬🇧"]
    assert texts[0].startswith("🔮 Main menu")
    user = await _get_user(sessionmaker, 1)
    assert user is not None and user.language == "en"


async def test_delete_me_removes_everything(harness: BotHarness, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    await _onboard(harness, user_id=1)
    await harness.send("/start ref_1", user_id=2)
    await harness.send("/delete_me", user_id=2)
    await harness.press(DeleteCb(confirm=True).pack(), user_id=2)
    assert harness.edited_texts()[0].startswith("Все твои данные удалены")

    async with sessionmaker() as session:
        assert await session.get(User, 2) is None
        assert (await session.execute(select(func.count()).select_from(Referral))).scalar() == 0
        events = (await session.execute(select(Event.user_id))).scalars().all()
        assert 2 not in events

    # После удаления можно начать заново.
    texts = await harness.send("/start", user_id=2)
    assert "Твой личный астролог" in texts[0]


async def test_coming_soon_sections(harness: BotHarness) -> None:
    await _onboard(harness)
    harness.session.clear()
    await harness.press(MenuCb(section="spreads").pack())
    answers = [r for r in harness.session.requests if type(r).__name__ == "AnswerCallbackQuery"]
    assert answers[0].text == "✨ Этот раздел появится совсем скоро!"
