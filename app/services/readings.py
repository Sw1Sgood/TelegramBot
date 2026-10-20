"""Расклады таро: выбор карт, трактовка (ИИ или готовые тексты) и сохранение в дневник."""

import json
import logging
import secrets
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import repo
from app.db.models import Reading, User
from app.i18n import Translator
from app.services import tarot
from app.services.astrology import ZodiacSign
from app.services.llm import LLM, LLMUnavailable
from app.services.tarot import DrawnCard

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
QUESTION_POSITIONS = ("past", "present", "future")
HISTORY_SIZE = 3

_random = secrets.SystemRandom()


@dataclass(frozen=True)
class ReadingResult:
    reading: Reading
    cards: list[DrawnCard]
    text: str  # готовый к отправке HTML
    used_ai: bool


@lru_cache
def load_prompt(lang: str, name: str) -> str:
    path = PROMPTS_DIR / lang / f"{name}.txt"
    if not path.exists():
        path = PROMPTS_DIR / "ru" / f"{name}.txt"
    return path.read_text(encoding="utf-8")


@lru_cache
def _advice() -> dict[str, dict[str, dict[str, list[str]]]]:
    return json.loads((tarot.DECK_DIR / "advice.json").read_text(encoding="utf-8"))


def card_advice(lang: str, drawn: DrawnCard) -> str:
    pool = _advice().get(lang) or _advice()["ru"]
    return _random.choice(pool[drawn.card.suit or "major"]["rev" if drawn.is_reversed else "up"])


def card_label(t: Translator, drawn: DrawnCard) -> str:
    """«Прошлое — Звезда (перевёрнутая)»; без позиции — только название."""
    name = drawn.card.name(t.locale)
    if drawn.is_reversed:
        name = f"{name} ({t('card-reversed')})"
    if drawn.position:
        return f"{t(f'position-{drawn.position}')} — {name}"
    return name


def day_bounds_utc(day: date, tz_name: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(tz_name)
    start = datetime.combine(day, time.min, tzinfo=tz)
    return start.astimezone(timezone.utc), (start + timedelta(days=1)).astimezone(timezone.utc)


# --- Готовые тексты ---------------------------------------------------------------------------


def template_daily(t: Translator, drawn: DrawnCard) -> str:
    return (
        f"{t('daily-card-title', card=escape(card_label(t, drawn)))}\n\n"
        f"{escape(drawn.card.meaning(t.locale, drawn.is_reversed))}\n\n"
        f"<b>{t('daily-advice-label')}</b> {escape(card_advice(t.locale, drawn))}"
    )


def template_question(t: Translator, user: User, question: str, cards: list[DrawnCard]) -> str:
    parts = [
        _question_header(t, question),
        t("reading-intro", name=escape(user.name or "")),
    ]
    for drawn in cards:
        parts.append(f"<b>{escape(card_label(t, drawn))}</b>\n{escape(drawn.card.meaning(t.locale, drawn.is_reversed))}")
    # Совет — от карты настоящего: она про то, что можно сделать сейчас.
    parts.append(f"<b>{t('advice-label')}</b> {escape(card_advice(t.locale, cards[1]))}")
    return "\n\n".join(parts)


def _question_header(t: Translator, question: str) -> str:
    return f"<b>{t('reading-question-title')}</b>\n<i>«{escape(question)}»</i>"


# --- ИИ ---------------------------------------------------------------------------------------


def _profile_block(t: Translator, user: User) -> str:
    sign = t(f"zodiac-{ZodiacSign(user.zodiac_sign).value}") if user.zodiac_sign else "—"
    return t(
        "llm-profile",
        name=user.name or "—",
        sign=sign,
        life_path=str(user.life_path_number or "—"),
    )


def _history_block(t: Translator, history: list[Reading]) -> str:
    if not history:
        return t("llm-history-empty")
    lines = []
    for reading in history:
        cards = ", ".join(card_label(t, d) for d in tarot.from_json(reading.cards))
        kind = t(f"llm-reading-type-{reading.type}")
        question = f" «{reading.question}»" if reading.question else ""
        lines.append(f"- {reading.created_at:%d.%m.%Y}, {kind}{question}: {cards}")
    return t("llm-history", items="\n".join(lines))


def _cards_block(t: Translator, cards: list[DrawnCard]) -> str:
    return "\n".join(
        f"{i}. {card_label(t, d)}. {t('llm-base-meaning')}: {d.card.meaning(t.locale, d.is_reversed)}"
        for i, d in enumerate(cards, start=1)
    )


class ReadingService:
    def __init__(self, settings: Settings, llm: LLM) -> None:
        self.settings = settings
        self.llm = llm

    async def _can_use_ai(self, day: date, premium: bool) -> bool:
        if not self.llm.enabled:
            return False
        # При превышении дневного бюджета платные расклады продолжают идти через ИИ.
        return premium or not await self.llm.over_budget(day)

    async def todays_daily_card(self, session: AsyncSession, user: User, today: date) -> Reading | None:
        start, end = day_bounds_utc(today, user.timezone)
        return await repo.find_reading_between(session, user.id, "daily", start, end)

    async def daily_card(
        self, session: AsyncSession, user: User, t: Translator, today: date, premium: bool
    ) -> ReadingResult:
        cards = tarot.draw(1)
        text = None
        tokens_in = tokens_out = 0
        cost = 0
        if await self._can_use_ai(today, premium):
            prompt = "\n\n".join(
                [
                    t("llm-daily-task", date=today.strftime("%d.%m.%Y")),
                    _profile_block(t, user),
                    _cards_block(t, cards),
                ]
            )
            try:
                result = await self.llm.generate(load_prompt(t.locale, "tarot"), prompt, today)
            except LLMUnavailable:
                pass
            else:
                text = f"{t('daily-card-title', card=escape(card_label(t, cards[0])))}\n\n{escape(result.text)}"
                tokens_in, tokens_out, cost = result.tokens_in, result.tokens_out, result.cost_usd
        used_ai = text is not None
        if text is None:
            text = template_daily(t, cards[0])
        reading = await self._save(session, user, "daily", None, cards, text, tokens_in, tokens_out, cost)
        return ReadingResult(reading, cards, text, used_ai)

    async def question(
        self, session: AsyncSession, user: User, t: Translator, question: str, today: date, premium: bool
    ) -> ReadingResult:
        cards = tarot.draw(3, QUESTION_POSITIONS)
        text = None
        tokens_in = tokens_out = 0
        cost = 0
        if await self._can_use_ai(today, premium):
            history = await repo.recent_readings(session, user.id, HISTORY_SIZE)
            prompt = "\n\n".join(
                [
                    t("llm-question-task", date=today.strftime("%d.%m.%Y")),
                    _profile_block(t, user),
                    _history_block(t, history),
                    t("llm-question", question=question),
                    _cards_block(t, cards),
                ]
            )
            try:
                result = await self.llm.generate(load_prompt(t.locale, "tarot"), prompt, today)
            except LLMUnavailable:
                pass
            else:
                text = f"{_question_header(t, question)}\n\n{escape(result.text)}"
                tokens_in, tokens_out, cost = result.tokens_in, result.tokens_out, result.cost_usd
        used_ai = text is not None
        if text is None:
            text = template_question(t, user, question, cards)
        reading = await self._save(session, user, "question", question, cards, text, tokens_in, tokens_out, cost)
        return ReadingResult(reading, cards, text, used_ai)

    async def _save(
        self,
        session: AsyncSession,
        user: User,
        reading_type: str,
        question: str | None,
        cards: list[DrawnCard],
        text: str,
        tokens_in: int,
        tokens_out: int,
        cost: object,
    ) -> Reading:
        reading = await repo.add_reading(
            session,
            Reading(
                user_id=user.id,
                type=reading_type,
                question=question,
                cards=[d.to_json() for d in cards],
                response_text=text,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_usd=cost,
                created_at=datetime.now(timezone.utc),
            ),
        )
        await repo.log_event(session, user.id, "reading", {"type": reading_type, "ai": tokens_out > 0})
        return reading
