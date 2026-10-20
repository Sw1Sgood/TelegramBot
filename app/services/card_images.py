"""Картинки карт для отправки в Telegram.

Перевёрнутые карты поворачиваются на 180° и кэшируются на диске. После первой отправки
Telegram выдаёт file_id — он сохраняется в Redis, и повторно файл уже не загружается.
"""

import logging
import tempfile
from pathlib import Path

from aiogram.types import FSInputFile
from PIL import Image
from redis.asyncio import Redis

from app.services.tarot import DrawnCard

logger = logging.getLogger(__name__)

ROTATED_DIR = Path(tempfile.gettempdir()) / "astro-bot-cards"


class CardImages:
    def __init__(self, redis: Redis, bot_id: int) -> None:
        self.redis = redis
        # file_id привязан к боту, поэтому ключ включает его id.
        self.prefix = f"cardimg:{bot_id}"

    def _key(self, drawn: DrawnCard) -> str:
        return f"{self.prefix}:{drawn.card.id}:{int(drawn.is_reversed)}"

    def _file(self, drawn: DrawnCard) -> Path | None:
        source = drawn.card.image_path
        if not source.exists():
            return None
        if not drawn.is_reversed:
            return source
        target = ROTATED_DIR / f"{drawn.card.id}_rev.jpg"
        if not target.exists():
            ROTATED_DIR.mkdir(parents=True, exist_ok=True)
            with Image.open(source) as image:
                image.rotate(180).save(target, quality=88)
        return target

    async def media(self, drawn: DrawnCard) -> str | FSInputFile | None:
        """file_id из кэша, файл с диска или None, если картинки нет."""
        cached = await self.redis.get(self._key(drawn))
        if cached:
            return cached.decode() if isinstance(cached, bytes) else cached
        try:
            path = self._file(drawn)
        except OSError:
            logger.warning("Could not prepare image for %s", drawn.card.id, exc_info=True)
            return None
        return FSInputFile(path) if path else None

    async def remember(self, drawn: DrawnCard, file_id: str) -> None:
        await self.redis.set(self._key(drawn), file_id)
