from datetime import date

from app.i18n import I18n
from app.services import tarot
from app.services.horoscope import Period, personal_number, template_body
from app.services.astrology import ZodiacSign
from app.services.readings import card_advice, card_label, template_daily
from app.services.safety import is_crisis
from app.services.tarot import DrawnCard


def test_deck_is_complete() -> None:
    deck = tarot.load_deck()
    assert len(deck) == 78
    assert sum(1 for card in deck.values() if card.suit is None) == 22
    for card in deck.values():
        for lang in ("ru", "en"):
            assert card.name(lang) and card.meaning(lang, False) and card.meaning(lang, True)


def test_minor_names() -> None:
    assert tarot.get_card("cups_01").name("ru") == "Туз Кубков"
    assert tarot.get_card("swords_13").name("en") == "Queen of Swords"
    assert tarot.get_card("pentacles_11").name("ru") == "Паж Пентаклей"


def test_draw_gives_distinct_cards_with_positions() -> None:
    for _ in range(200):
        cards = tarot.draw(3, ("past", "present", "future"))
        assert len({d.card.id for d in cards}) == 3
        assert [d.position for d in cards] == ["past", "present", "future"]


def test_reversed_probability_is_about_30_percent() -> None:
    reversed_count = sum(d.is_reversed for _ in range(2000) for d in tarot.draw(1))
    assert 450 < reversed_count < 750


def test_json_roundtrip() -> None:
    cards = tarot.draw(3, ("past", "present", "future"))
    assert tarot.from_json([d.to_json() for d in cards]) == cards


def test_labels_and_templates() -> None:
    t = I18n().translator("ru")
    drawn = DrawnCard(tarot.get_card("major_17"), True, "past")
    assert card_label(t, drawn) == "Прошлое — Звезда (перевёрнутая)"
    text = template_daily(t, DrawnCard(tarot.get_card("major_19"), False))
    assert "Карта дня — Солнце" in text and "Совет дня:" in text
    assert card_advice("en", drawn)


def test_horoscope_template_is_stable_per_sign_and_day() -> None:
    t = I18n().translator("ru")
    day = Period.for_day("day", date(2026, 10, 20))
    first = template_body(t, ZodiacSign.ARIES, day)
    assert first == template_body(t, ZodiacSign.ARIES, day)
    assert first != template_body(t, ZodiacSign.ARIES, Period.for_day("day", date(2026, 10, 21)))
    for label in ("Настроение:", "Любовь:", "Работа и деньги:", "Совет:", "Цвет удачи"):
        assert label in first


def test_periods() -> None:
    week = Period.for_day("week", date(2026, 10, 22))  # четверг
    assert (week.start, week.end) == (date(2026, 10, 19), date(2026, 10, 25))
    month = Period.for_day("month", date(2026, 2, 10))
    assert (month.start, month.end) == (date(2026, 2, 1), date(2026, 2, 28))


def test_personal_number_range() -> None:
    birth = date(1995, 3, 25)
    for offset in range(60):
        day = date.fromordinal(date(2026, 1, 1).toordinal() + offset)
        assert 1 <= personal_number(birth, Period.for_day("day", day)) <= 9


def test_crisis_detection() -> None:
    assert is_crisis("Я не хочу жить, что меня ждёт?")
    assert is_crisis("думаю о самоубийстве")
    assert is_crisis("I want to die")
    assert not is_crisis("Что меня ждёт в отношениях с Сашей?")
    assert not is_crisis("Стоит ли менять работу?")
