import pytest

from barber_bot.services.idempotency import consume_update_id


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int, nx: bool) -> bool:
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True


@pytest.mark.asyncio
async def test_update_id_idempotency() -> None:
    redis = FakeRedis()

    first = await consume_update_id(redis, update_id=101, ttl_seconds=60)
    second = await consume_update_id(redis, update_id=101, ttl_seconds=60)

    assert first is True
    assert second is False
