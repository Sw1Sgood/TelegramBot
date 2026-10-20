"""Единая точка вызова ИИ: таймаут, ретраи, параллелизм и учёт стоимости."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import anthropic
from redis.asyncio import Redis

from app.config import Settings

logger = logging.getLogger(__name__)


class LLMUnavailable(Exception):
    """ИИ недоступен: нет ключа, превышен бюджет или запрос не удался."""


@dataclass(frozen=True)
class LLMResult:
    text: str
    tokens_in: int
    tokens_out: int
    cost_usd: Decimal


class LLM:
    def __init__(self, settings: Settings, redis: Redis) -> None:
        self.settings = settings
        self.redis = redis
        api_key = settings.anthropic_api_key.get_secret_value()
        self._client = (
            anthropic.AsyncAnthropic(
                api_key=api_key, timeout=settings.llm_timeout_seconds, max_retries=settings.llm_max_retries
            )
            if api_key
            else None
        )
        self._semaphore = asyncio.Semaphore(settings.llm_max_concurrency)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    @property
    def is_busy(self) -> bool:
        """Все слоты заняты — новый запрос встанет в очередь."""
        return self._semaphore.locked()

    @staticmethod
    def _budget_key(day: date) -> str:
        return f"llm:cost:{day.isoformat()}"

    async def spent_today(self, day: date) -> float:
        return float(await self.redis.get(self._budget_key(day)) or 0)

    async def over_budget(self, day: date) -> bool:
        return await self.spent_today(day) >= self.settings.llm_daily_budget_usd

    async def generate(self, system: str, prompt: str, day: date, max_tokens: int = 4000) -> LLMResult:
        if self._client is None:
            raise LLMUnavailable("no api key")
        async with self._semaphore:
            try:
                response = await self._client.messages.create(
                    model=self.settings.llm_model,
                    max_tokens=max_tokens,
                    system=system,
                    output_config={"effort": "low"},
                    messages=[{"role": "user", "content": prompt}],
                )
            except anthropic.APIError as error:
                logger.warning("LLM request failed: %s", error)
                raise LLMUnavailable(str(error)) from error

        if response.stop_reason == "refusal":
            raise LLMUnavailable("refusal")
        text = "\n".join(block.text for block in response.content if block.type == "text").strip()
        if not text:
            raise LLMUnavailable("empty response")

        usage = response.usage
        cost = Decimal(str(
            usage.input_tokens * self.settings.llm_price_input_per_mtok / 1_000_000
            + usage.output_tokens * self.settings.llm_price_output_per_mtok / 1_000_000
        ))
        key = self._budget_key(day)
        await self.redis.incrbyfloat(key, float(cost))
        await self.redis.expire(key, 3 * 24 * 3600)
        return LLMResult(text, usage.input_tokens, usage.output_tokens, cost)
