from fluent.syntax import parse
from fluent.syntax.ast import Message

from app.i18n import LOCALES_DIR, I18n
from app.services.astrology import ZodiacSign


def _keys(locale: str) -> set[str]:
    keys: set[str] = set()
    for ftl in (LOCALES_DIR / locale).glob("*.ftl"):
        resource = parse(ftl.read_text(encoding="utf-8"))
        keys |= {entry.id.name for entry in resource.body if isinstance(entry, Message)}
    return keys


def test_locales_have_same_keys() -> None:
    assert _keys("ru") == _keys("en")


def test_no_syntax_errors() -> None:
    for locale in ("ru", "en"):
        for ftl in (LOCALES_DIR / locale).glob("*.ftl"):
            resource = parse(ftl.read_text(encoding="utf-8"))
            junk = [entry for entry in resource.body if type(entry).__name__ == "Junk"]
            assert not junk, f"{ftl}: {junk[0].content[:80]}"


def test_dynamic_keys_exist() -> None:
    keys = _keys("ru")
    for sign in ZodiacSign:
        assert f"zodiac-{sign.value}" in keys
    for number in (*range(1, 10), 11, 22, 33):
        assert f"lifepath-{number}" in keys


def test_translator_formats_and_falls_back() -> None:
    i18n = I18n(default_locale="ru", global_args={"bot_name": "Твой личный астролог"})
    assert "«Твой личный астролог»" in i18n.translator("en")("start-greeting")
    assert "Анна" in i18n.translator("ru")("ask-birth-date", name="Анна")
    # Неизвестный язык — русский по умолчанию.
    assert i18n.translator("de").locale == "ru"
    assert i18n.translator("ru")("no-such-key") == "no-such-key"
