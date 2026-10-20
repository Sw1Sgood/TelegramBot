"""Совместимость пары по знакам зодиака и числам жизненного пути."""

import hashlib
from dataclasses import dataclass
from datetime import date

from app.services.astrology import ZodiacSign, zodiac_sign
from app.services.horoscope import ELEMENTS
from app.services.numerology import MASTER_NUMBERS, life_path_number, reduce_number

# Огонь с воздухом и земля с водой поддерживают друг друга, одна стихия — понимание с полуслова.
_ELEMENT_SCORES = {
    frozenset({"fire"}): 85, frozenset({"earth"}): 85, frozenset({"air"}): 85, frozenset({"water"}): 85,
    frozenset({"fire", "air"}): 90, frozenset({"earth", "water"}): 90,
    frozenset({"fire", "earth"}): 60, frozenset({"air", "water"}): 60,
    frozenset({"fire", "water"}): 50, frozenset({"earth", "air"}): 55,
}
# Группы чисел пути со схожим ритмом жизни.
_NUMBER_GROUPS = ({1, 5, 7}, {2, 4, 8}, {3, 6, 9})


@dataclass(frozen=True)
class Compatibility:
    sign_a: ZodiacSign
    sign_b: ZodiacSign
    life_path_a: int
    life_path_b: int
    element_pair: str  # ключ вида "air-fire"
    numbers_harmonious: bool
    score: int


def _base(number: int) -> int:
    return reduce_number(number, keep_master=False) if number in MASTER_NUMBERS else number


def calculate(birth_a: date, birth_b: date) -> Compatibility:
    sign_a, sign_b = zodiac_sign(birth_a), zodiac_sign(birth_b)
    lp_a, lp_b = life_path_number(birth_a), life_path_number(birth_b)
    elements = frozenset({ELEMENTS[sign_a], ELEMENTS[sign_b]})
    element_score = _ELEMENT_SCORES[elements]
    harmonious = any(_base(lp_a) in group and _base(lp_b) in group for group in _NUMBER_GROUPS)
    number_score = 90 if harmonious else 65
    # Небольшая поправка, чтобы у разных пар одной стихии проценты отличались.
    pair = "-".join(sorted((birth_a.isoformat(), birth_b.isoformat())))
    tweak = int(hashlib.sha256(pair.encode()).hexdigest(), 16) % 11 - 5
    score = max(35, min(98, round(element_score * 0.6 + number_score * 0.4) + tweak))
    element_pair = "-".join(sorted(elements)) if len(elements) == 2 else next(iter(elements)) + "-" + next(iter(elements))
    return Compatibility(sign_a, sign_b, lp_a, lp_b, element_pair, harmonious, score)
