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
HISTORY_SIZE = 3


@dataclass(frozen=True)
class Spread:
    kind: str
    positions: tuple[str, ...]
    advice_index: int  # карта, от которой даётся совет в готовых текстах
    premium: bool


SPREADS: dict[str, Spread] = {
    "question": Spread("question", ("past", "present", "future"), 1, premium=False),
    "yesno": Spread("yesno", ("answer",), 0, premium=True),
    "two-paths": Spread("two-paths", ("path-a", "path-b", "advice"), 2, premium=True),
    "relationship": Spread("relationship", ("you", "partner", "connection", "obstacle", "potential"), 4, premium=True),
    "celtic": Spread(
        "celtic",
        ("situation", "challenge", "past", "future", "goal", "foundation", "self", "environment", "hopes", "outcome"),
        6,
        premium=True,
    ),
}
BIG_SPREADS = ("celtic", "relationship", "yesno", "two-paths")

# Карты, которые в раскладе «Да/Нет» в прямом положении означают «пока неясно».
_UNCLEAR_CARDS = frozenset({"major_02", "major_10", "major_12", "major_18", "swords_02", "cups_07", "pentacles_02"})


def yes_no_verdict(drawn: DrawnCard) -> str:
    if drawn.is_reversed:
        return "no"
    if drawn.card.id in _UNCLEAR_CARDS:
        return "maybe"
    return "yes"

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


def template_spread(t: Translator, user: User, spread: Spread, question: str, cards: list[DrawnCard]) -> str:
    parts = [_spread_header(t, spread, question), t("reading-intro", name=escape(user.name or ""))]
    if spread.kind == "yesno":
        parts.append(f"<b>{t('yesno-verdict-' + yes_no_verdict(cards[0]))}</b>")
    for drawn in cards:
        parts.append(f"<b>{escape(card_label(t, drawn))}</b>\n{escape(drawn.card.meaning(t.locale, drawn.is_reversed))}")
    parts.append(f"<b>{t('advice-label')}</b> {escape(card_advice(t.locale, cards[spread.advice_index]))}")
    return "\n\n".join(parts)


def _spread_header(t: Translator, spread: Spread, question: str) -> str:
    return f"<b>{t('spread-title-' + spread.kind)}</b>\n<i>«{escape(question)}»</i>"


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

    async def spread(
        self,
        session: AsyncSession,
        user: User,
        t: Translator,
        spread: Spread,
        question: str,
        today: date,
        premium: bool,
    ) -> ReadingResult:
        cards = tarot.draw(len(spread.positions), spread.positions)
        text = None
        tokens_in = tokens_out = 0
        cost = 0
        if await self._can_use_ai(today, premium):
            history = await repo.recent_readings(session, user.id, HISTORY_SIZE)
            prompt = "\n\n".join(
                [
                    t(f"llm-task-{spread.kind}", date=today.strftime("%d.%m.%Y")),
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
                text = f"{_spread_header(t, spread, question)}\n\n{escape(result.text)}"
                tokens_in, tokens_out, cost = result.tokens_in, result.tokens_out, result.cost_usd
        used_ai = text is not None
        if text is None:
            text = template_spread(t, user, spread, question, cards)
        reading = await self._save(session, user, spread.kind, question, cards, text, tokens_in, tokens_out, cost)
        return ReadingResult(reading, cards, text, used_ai)

    async def save_text_reading(
        self,
        session: AsyncSession,
        user: User,
        reading_type: str,
        question: str | None,
        text: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost: object = 0,
    ) -> Reading:
        """Сохраняет в дневник разбор без карт (совместимость, сон)."""
        return await self._save(session, user, reading_type, question, [], text, tokens_in, tokens_out, cost)

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
