"""Колода таро: данные карт и случайный выбор."""

import json
import secrets
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
DECK_DIR = ASSETS_DIR / "tarot"
CARDS_DIR = ASSETS_DIR / "cards"

REVERSED_PROBABILITY = 0.3
SUITS = ("wands", "cups", "swords", "pentacles")

_RANKS = {
    "ru": ("Туз", "Двойка", "Тройка", "Четвёрка", "Пятёрка", "Шестёрка", "Семёрка", "Восьмёрка", "Девятка",
           "Десятка", "Паж", "Рыцарь", "Королева", "Король"),
    "en": ("Ace", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Page", "Knight",
           "Queen", "King"),
}
_SUIT_NAMES = {
    "ru": {"wands": "Жезлов", "cups": "Кубков", "swords": "Мечей", "pentacles": "Пентаклей"},
    "en": {"wands": "Wands", "cups": "Cups", "swords": "Swords", "pentacles": "Pentacles"},
}

_random = secrets.SystemRandom()


@dataclass(frozen=True)
class Card:
    id: str
    suit: str | None  # None — старший аркан
    names: dict[str, str]
    upright: dict[str, str]
    reversed: dict[str, str]

    def name(self, lang: str) -> str:
        return self.names.get(lang) or self.names["ru"]

    def meaning(self, lang: str, is_reversed: bool) -> str:
        source = self.reversed if is_reversed else self.upright
        return source.get(lang) or source["ru"]

    @property
    def image_path(self) -> Path:
        return CARDS_DIR / f"{self.id}.jpg"


@dataclass(frozen=True)
class DrawnCard:
    card: Card
    is_reversed: bool
    position: str | None = None  # ключ позиции в раскладе: past / present / future

    def to_json(self) -> dict[str, object]:
        return {"card": self.card.id, "reversed": self.is_reversed, "position": self.position}


@lru_cache
def load_deck() -> dict[str, Card]:
    deck: dict[str, Card] = {}
    for item in json.loads((DECK_DIR / "major.json").read_text(encoding="utf-8")):
        deck[item["id"]] = Card(item["id"], None, item["name"], item["up"], item["rev"])
    for suit in SUITS:
        for item in json.loads((DECK_DIR / f"{suit}.json").read_text(encoding="utf-8")):
            rank = int(item["id"].split("_")[1])
            names = {
                "ru": f"{_RANKS['ru'][rank - 1]} {_SUIT_NAMES['ru'][suit]}",
                "en": f"{_RANKS['en'][rank - 1]} of {_SUIT_NAMES['en'][suit]}",
            }
            deck[item["id"]] = Card(item["id"], suit, names, item["up"], item["rev"])
    return deck


def get_card(card_id: str) -> Card:
    return load_deck()[card_id]


def draw(count: int, positions: tuple[str, ...] | None = None) -> list[DrawnCard]:
    """Тянет count разных карт; каждая может выпасть перевёрнутой."""
    cards = _random.sample(list(load_deck().values()), count)
    return [
        DrawnCard(card, _random.random() < REVERSED_PROBABILITY, positions[i] if positions else None)
        for i, card in enumerate(cards)
    ]


def from_json(items: list[dict[str, object]]) -> list[DrawnCard]:
    return [DrawnCard(get_card(str(i["card"])), bool(i["reversed"]), i.get("position")) for i in items]  # type: ignore[arg-type]
