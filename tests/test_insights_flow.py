from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import repo
from app.db.models import Reading, Referral
from app.keyboards import MenuCb, SpreadCb
from app.services import compatibility, numerology
from app.services.dreams import find_symbols
from app.services.readings import yes_no_verdict
from app.services import tarot
from tests.conftest import BotHarness
from tests.test_onboarding_flow import _onboard


async def _readings(sessionmaker: async_sessionmaker[AsyncSession]) -> list[Reading]:
    async with sessionmaker() as session:
        return list((await session.execute(select(Reading).order_by(Reading.id))).scalars())


async def _give_credits(sessionmaker: async_sessionmaker[AsyncSession], user_id: int, amount: int) -> None:
    async with sessionmaker() as session:
        await repo.add_credits(session, user_id, amount)
        await session.commit()


async def _credits(sessionmaker: async_sessionmaker[AsyncSession], user_id: int) -> int:
    async with sessionmaker() as session:
        return await repo.get_credits(session, user_id)


# --- Сервисы -----------------------------------------------------------------------------------


def test_name_numbers() -> None:
    # А=1 Н=6 Н=6 А=1 → 14 → 5; гласные А+А = 2; согласные Н+Н = 12 → 3
    assert numerology.expression_number("Анна") == 5
    assert numerology.soul_number("Анна") == 2
    assert numerology.personality_number("Анна") == 3
    # J=1 O=6 H=8 N=5 → 20 → 2
    assert numerology.expression_number("John") == 2
    assert not numerology.has_letters("123")


def test_compatibility_is_symmetric_and_bounded() -> None:
    a, b = date(1995, 3, 25), date(1992, 8, 1)
    first, second = compatibility.calculate(a, b), compatibility.calculate(b, a)
    assert first.score == second.score
    assert first.element_pair == "fire-fire"  # Овен и Лев
    assert 35 <= first.score <= 98


def test_dream_symbols() -> None:
    found = find_symbols("Мне снилось, что я летала над морем, а потом за мной гналась собака", "ru")
    assert [entry["symbol"] for entry in found] == ["Полёт", "Вода", "Погоня"]
    assert find_symbols("ничего особенного", "ru") == []


def test_yes_no_verdict() -> None:
    assert yes_no_verdict(tarot.DrawnCard(tarot.get_card("major_19"), False)) == "yes"
    assert yes_no_verdict(tarot.DrawnCard(tarot.get_card("major_19"), True)) == "no"
    assert yes_no_verdict(tarot.DrawnCard(tarot.get_card("major_18"), False)) == "maybe"


# --- Диалоги -----------------------------------------------------------------------------------


async def test_big_spreads_are_locked_without_access(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness)
    texts = await harness.press(MenuCb(section="spreads").pack())
    assert texts[0].startswith("🌟 Большие расклады")
    markup = harness.session.of_type("SendMessage")[0].reply_markup
    assert all("🔒" in row[0].text for row in markup.inline_keyboard[:4])

    await harness.press(SpreadCb(kind="celtic").pack())
    texts = await harness.send("Что происходит с моей карьерой?")
    assert texts[0].startswith("🔒 Этот раздел доступен по подписке")
    assert [r.type for r in await _readings(sessionmaker)] == ["daily"]


async def test_celtic_cross_with_premium(harness: BotHarness, settings, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    settings.premium_for_all = True
    await _onboard(harness)
    await harness.press(SpreadCb(kind="celtic").pack())
    texts = await harness.send("Что происходит с моей карьерой?")
    groups = harness.session.of_type("SendMediaGroup")
    assert len(groups) == 1 and len(groups[0].media) == 10
    text = next(t for t in texts if "Кельтский крест" in t)
    for label in ("Ситуация — ", "Препятствие — ", "Итог — ", "Совет:"):
        assert label in text
    assert (await _readings(sessionmaker))[-1].type == "celtic"


async def test_yes_no_with_credit(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness)
    await _give_credits(sessionmaker, 1, 1)
    await harness.press(SpreadCb(kind="yesno").pack())
    texts = await harness.send("Стоит ли идти на встречу?")
    text = next(t for t in texts if "Да или нет" in t)
    assert any(v in text for v in ("Скорее да", "Скорее нет", "Пока неясно"))
    assert texts[-1] == "🎁 Использован бонусный расклад. Осталось: 0"
    assert await _credits(sessionmaker, 1) == 0


async def test_credit_is_used_after_free_question(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness)
    await _give_credits(sessionmaker, 1, 2)
    await harness.press(MenuCb(section="question").pack())
    await harness.send("Первый вопрос?")
    await harness.redis.delete("rate:1")
    await harness.press(MenuCb(section="question").pack())
    texts = await harness.send("Второй вопрос?")
    assert any("Расклад на вопрос" in t for t in texts)
    assert await _credits(sessionmaker, 1) == 1


async def test_compatibility(harness: BotHarness, settings, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    settings.premium_for_all = True
    await _onboard(harness)
    texts = await harness.press(MenuCb(section="compatibility").pack())
    assert "дату рождения партнёра" in texts[0]
    assert (await harness.send("32.13.1990"))[0].startswith("Такой даты не существует")
    texts = await harness.send("01.08.1992")
    assert "Совместимость: " in texts[0] and "♌ Лев" in texts[0] and "По стихиям:" in texts[0]
    reading = (await _readings(sessionmaker))[-1]
    assert (reading.type, reading.question, reading.cards) == ("compatibility", "01.08.1992", [])


async def test_numerology_basic_and_full(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness)
    texts = await harness.press(MenuCb(section="numerology").pack())
    assert "Число жизненного пути — 7" in texts[0]
    assert "Число судьбы" not in texts[0] and "🔒 Полный разбор" in texts[0]

    texts = await harness.press(MenuCb(section="numerology-full").pack())
    assert texts[0].startswith("🔒")

    await _give_credits(sessionmaker, 1, 1)
    texts = await harness.press(MenuCb(section="numerology-full").pack())
    assert "Число судьбы (по имени) — 5" in texts[0] and "Число души — 2" in texts[0]


async def test_dream_interpretation(harness: BotHarness, settings, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    settings.premium_for_all = True
    await _onboard(harness)
    texts = await harness.press(MenuCb(section="dreams").pack())
    assert texts[0].startswith("🌙 Опиши свой сон")
    texts = await harness.send("Мне снилось, что я летала над морем")
    text = next(t for t in texts if "Толкование сна" in t)
    assert "<b>Полёт</b>" in text and "<b>Вода</b>" in text
    assert (await _readings(sessionmaker))[-1].type == "dream"


async def test_referral_reward_once_with_notification(harness: BotHarness, sessionmaker) -> None:  # type: ignore[no-untyped-def]
    await _onboard(harness, user_id=1)
    texts = await harness.press(MenuCb(section="invite").pack())
    assert "https://t.me/test_bot?start=ref_1" in texts[0]

    await _onboard(harness, user_id=2, start="/start ref_1")
    assert await _credits(sessionmaker, 1) == 0  # Карта дня при знакомстве не считается

    await harness.press(MenuCb(section="question").pack(), user_id=2)
    harness.session.clear()
    await harness.send("Что меня ждёт?", user_id=2)
    notices = [r for r in harness.session.of_type("SendMessage") if int(r.chat_id) == 1]
    assert notices and "начислено 3 бонусных расклада" in notices[0].text
    assert await _credits(sessionmaker, 1) == 3

    # Повторные расклады друга бонус не дают.
    await harness.redis.delete("rate:2")
    await _give_credits(sessionmaker, 2, 1)
    await harness.press(MenuCb(section="question").pack(), user_id=2)
    await harness.send("И ещё вопрос?", user_id=2)
    assert await _credits(sessionmaker, 1) == 3
    async with sessionmaker() as session:
        referral = (await session.execute(select(Referral))).scalar_one()
        assert referral.rewarded_at is not None

    texts = await harness.press(MenuCb(section="invite").pack(), user_id=1)
    assert "Пришли друзей: 1" in texts[0] and "Бонусных раскладов на счету: 3" in texts[0]
