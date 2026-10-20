from datetime import time
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: SecretStr
    # Имя бота одно для всех языков интерфейса — на русском.
    bot_name: str = "Твой личный астролог | Таро и гороскоп"
    bot_username: str = "TaroAstrologiaGoroskopBot"

    run_mode: Literal["polling", "webhook"] = "polling"
    webhook_base_url: str = ""
    webhook_path: str = "/webhook"
    webhook_secret: SecretStr = SecretStr("")
    web_host: str = "0.0.0.0"
    web_port: int = 8080

    database_url: str = "postgresql+asyncpg://astro:astro@postgres:5432/astro"
    redis_url: str = "redis://redis:6379/0"

    default_language: Literal["ru", "en"] = "ru"
    default_timezone: str = "Europe/Moscow"
    default_daily_card_time: time = time(9, 0)

    # ИИ-трактовки. Без ключа бот пишет трактовки из готовых текстов.
    anthropic_api_key: SecretStr = SecretStr("")
    llm_model: str = "claude-haiku-5-5"
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2
    llm_max_concurrency: int = 50
    # Цены модели за 1 млн токенов, $ — для учёта расходов.
    llm_price_input_per_mtok: float = 0.10
    llm_price_output_per_mtok: float = 0.50
    # Дневной бюджет на ИИ, $. При превышении бесплатные расклады идут на готовых текстах.
    llm_daily_budget_usd: float = 5.0

    # Лимиты раскладов.
    free_questions_per_day: int = 1
    premium_readings_per_day: int = 30
    llm_rate_limit_seconds: int = 5
    question_max_length: int = 500
    # Открыть всем платные разделы (для демо, пока нет оплаты).
    premium_for_all: bool = False

    admin_ids: Annotated[list[int], NoDecode] = []
    log_level: str = "INFO"

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _split_ids(cls, value: object) -> object:
        if isinstance(value, str):
            return [int(part) for part in value.replace(" ", "").split(",") if part]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
