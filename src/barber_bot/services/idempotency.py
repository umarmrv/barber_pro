from __future__ import annotations

from redis.asyncio import Redis


async def consume_update_id(redis: Redis, update_id: int, ttl_seconds: int) -> bool:
    key = f"telegram_update:{update_id}"
    return bool(await redis.set(key, "1", ex=ttl_seconds, nx=True))
