"""Гороскоп на день, неделю и месяц.

Общая часть гороскопа одна для всех людей одного знака на период: её пишет ИИ (и она кэшируется
в Redis) или она собирается из готовых фраз. Сверху добавляется личное число по дате рождения.
"""

import hashlib
import json
import random
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from html import escape

from redis.asyncio import Redis

from app.i18n import Translator
from app.services.astrology import ZODIAC_EMOJI, ZodiacSign
from app.services.llm import LLM, LLMUnavailable
from app.services.numerology import reduce_number
from app.services.readings import load_prompt
from app.services.tarot import ASSETS_DIR

PERIODS = ("day", "week", "month")

ELEMENTS = {
    ZodiacSign.ARIES: "fire", ZodiacSign.LEO: "fire", ZodiacSign.SAGITTARIUS: "fire",
    ZodiacSign.TAURUS: "earth", ZodiacSign.VIRGO: "earth", ZodiacSign.CAPRICORN: "earth",
    ZodiacSign.GEMINI: "air", ZodiacSign.LIBRA: "air", ZodiacSign.AQUARIUS: "air",
    ZodiacSign.CANCER: "water", ZodiacSign.SCORPIO: "water", ZodiacSign.PISCES: "water",
}


@lru_cache
def _phrases() -> dict[str, dict]:
    return json.loads((ASSETS_DIR / "horoscope.json").read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Period:
    kind: str
    start: date
    end: date  # включительно

    @classmethod
    def for_day(cls, kind: str, today: date) -> "Period":
        if kind == "week":
            start = today - timedelta(days=today.weekday())
            return cls(kind, start, start + timedelta(days=6))
        if kind == "month":
            start = today.replace(day=1)
            next_month = (start + timedelta(days=32)).replace(day=1)
            return cls(kind, start, next_month - timedelta(days=1))
        return cls("day", today, today)


def personal_number(birth_date: date, period: Period) -> int:
    """Личное число дня или месяца (нумерология, без мастер-чисел)."""
    personal_year = reduce_number(birth_date.day + birth_date.month + period.start.year, keep_master=False)
    personal_month = reduce_number(personal_year + period.start.month, keep_master=False)
    if period.kind == "month":
        return personal_month
    return reduce_number(personal_month + period.start.day, keep_master=False)


def template_body(t: Translator, sign: ZodiacSign, period: Period) -> str:
    phrases = _phrases().get(t.locale) or _phrases()["ru"]
    seed = hashlib.sha256(f"{sign.value}:{period.kind}:{period.start.isoformat()}".encode()).hexdigest()
    rng = random.Random(int(seed, 16))
    lines = [
        f"<b>{t('horo-mood')}</b> {escape(rng.choice(phrases['mood']))} {escape(rng.choice(phrases['element'][ELEMENTS[sign]]))}",
        f"<b>{t('horo-love')}</b> {escape(rng.choice(phrases['love']))}",
        f"<b>{t('horo-work')}</b> {escape(rng.choice(phrases['work']))}",
        f"<b>{t('horo-advice')}</b> {escape(rng.choice(phrases['advice']))}",
    ]
    extras = [
        t("horo-lucky-color", color=rng.choice(phrases["colors"])),
        t("horo-lucky-number", number=str(rng.randint(1, 99))),
    ]
    if period.kind == "week":
        extras.append(t("horo-lucky-day", day=rng.choice(phrases["weekdays"])))
    if period.kind == "month":
        lines.insert(0, f"<i>{escape(rng.choice(phrases['month_theme']))}</i>")
    return "\n\n".join(lines) + "\n\n" + "\n".join(extras)


class HoroscopeService:
    def __init__(self, llm: LLM, redis: Redis) -> None:
        self.llm = llm
        self.redis = redis

    def title(self, t: Translator, sign: ZodiacSign, period: Period) -> str:
        args = {"sign_emoji": ZODIAC_EMOJI[sign], "sign": t(f"zodiac-{sign.value}")}
        if period.kind == "week":
            return t("horo-title-week", start=period.start.strftime("%d.%m"), end=period.end.strftime("%d.%m"), **args)
        if period.kind == "month":
            return t("horo-title-month", month=t(f"month-{period.start.month}"), year=str(period.start.year), **args)
        return t("horo-title-day", date=period.start.strftime("%d.%m.%Y"), **args)

    async def _ai_body(self, t: Translator, sign: ZodiacSign, period: Period, today: date) -> str | None:
        if not self.llm.enabled or await self.llm.over_budget(today):
            return None
        key = f"horoscope:{t.locale}:{sign.value}:{period.kind}:{period.start.isoformat()}"
        if cached := await self.redis.get(key):
            return cached.decode() if isinstance(cached, bytes) else cached
        prompt = t(
            "llm-horoscope-task",
            sign=t(f"zodiac-{sign.value}"),
            period=t(f"llm-period-{period.kind}"),
            start=period.start.strftime("%d.%m.%Y"),
            end=period.end.strftime("%d.%m.%Y"),
        )
        try:
            result = await self.llm.generate(load_prompt(t.locale, "horoscope"), prompt, today)
        except LLMUnavailable:
            return None
        body = escape(result.text)
        ttl = (period.end - today).days * 86400 + 2 * 86400
        await self.redis.set(key, body, ex=ttl)
        return body

    async def render(self, t: Translator, sign: ZodiacSign, birth_date: date, period: Period, today: date) -> str:
        body = await self._ai_body(t, sign, period, today) or template_body(t, sign, period)
        number = personal_number(birth_date, period)
        personal = t(
            "horo-personal-month" if period.kind == "month" else "horo-personal-day",
            number=str(number),
            meaning=t(f"personal-{number}"),
        )
        return f"{self.title(t, sign, period)}\n\n{body}\n\n{personal}"
