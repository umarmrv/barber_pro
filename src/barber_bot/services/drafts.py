from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis


async def save_draft(redis: Redis, draft_id: str, payload: dict[str, Any], ttl_seconds: int) -> None:
    await redis.set(f"booking_draft:{draft_id}", json.dumps(payload), ex=ttl_seconds)


async def get_draft(redis: Redis, draft_id: str) -> dict[str, Any] | None:
    raw = await redis.get(f"booking_draft:{draft_id}")
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)
