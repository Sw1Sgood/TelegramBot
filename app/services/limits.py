"""Дневные лимиты и защита от слишком частых запросов (Redis)."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from redis.asyncio import Redis


def local_today(tz_name: str) -> date:
    return datetime.now(ZoneInfo(tz_name)).date()


def _end_of_day(day: date, tz_name: str) -> int:
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=ZoneInfo(tz_name))
    # Небольшой запас, чтобы ключ точно дожил до конца суток.
    return int(end.timestamp()) + 3600


class Limiter:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    @staticmethod
    def _key(user_id: int, day: date, kind: str) -> str:
        return f"limit:{user_id}:{day.isoformat()}:{kind}"

    async def try_consume(self, user_id: int, kind: str, limit: int, tz_name: str) -> bool:
        """Списывает одно использование; False — если лимит на сегодня исчерпан."""
        day = local_today(tz_name)
        key = self._key(user_id, day, kind)
        used = await self.redis.incr(key)
        if used == 1:
            await self.redis.expireat(key, _end_of_day(day, tz_name))
        if used > limit:
            await self.redis.decr(key)
            return False
        return True

    async def refund(self, user_id: int, kind: str, tz_name: str) -> None:
        key = self._key(user_id, local_today(tz_name), kind)
        if int(await self.redis.get(key) or 0) > 0:
            await self.redis.decr(key)

    async def used(self, user_id: int, kind: str, tz_name: str) -> int:
        return int(await self.redis.get(self._key(user_id, local_today(tz_name), kind)) or 0)

    async def hit_rate_limit(self, user_id: int, seconds: int) -> bool:
        """True — если пользователь уже делал запрос за последние seconds секунд."""
        return not await self.redis.set(f"rate:{user_id}", 1, ex=seconds, nx=True)
