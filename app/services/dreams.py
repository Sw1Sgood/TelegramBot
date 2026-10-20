"""Толкование снов без ИИ: поиск знакомых символов в описании сна."""

import json
import re
from functools import lru_cache

from app.services.tarot import ASSETS_DIR

MAX_SYMBOLS = 3


@lru_cache
def _dictionary() -> dict[str, list[dict]]:
    return json.loads((ASSETS_DIR / "dreams.json").read_text(encoding="utf-8"))


def find_symbols(text: str, lang: str) -> list[dict]:
    """Символы сна в порядке появления в тексте (не больше MAX_SYMBOLS)."""
    lowered = text.lower().replace("ё", "е")
    entries = _dictionary().get(lang) or _dictionary()["ru"]
    found = []
    for entry in entries:
        match = re.search(entry["pattern"], lowered)
        if match:
            found.append((match.start(), entry))
    return [entry for _, entry in sorted(found, key=lambda item: item[0])[:MAX_SYMBOLS]]
