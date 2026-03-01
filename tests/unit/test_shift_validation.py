from __future__ import annotations

from datetime import time

import pytest

from barber_bot.db.repositories import Repository


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    def __init__(self, overlap_id=None):
        self.overlap_id = overlap_id
        self.added = []

    async def execute(self, query):  # noqa: ARG002
        return _FakeResult(self.overlap_id)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_create_work_shift_rejects_invalid_range() -> None:
    session = _FakeSession(overlap_id=None)
    repo = Repository(session)

    shift = await repo.create_work_shift(
        barber_id=1,
        weekday=1,
        start_local_time=time(12, 0),
        end_local_time=time(11, 0),
    )

    assert shift is None
    assert session.added == []


@pytest.mark.asyncio
async def test_create_work_shift_rejects_overlapping_interval() -> None:
    session = _FakeSession(overlap_id=99)
    repo = Repository(session)

    shift = await repo.create_work_shift(
        barber_id=1,
        weekday=1,
        start_local_time=time(10, 0),
        end_local_time=time(13, 0),
    )

    assert shift is None
    assert session.added == []


@pytest.mark.asyncio
async def test_create_work_shift_accepts_non_overlapping_interval() -> None:
    session = _FakeSession(overlap_id=None)
    repo = Repository(session)

    shift = await repo.create_work_shift(
        barber_id=1,
        weekday=1,
        start_local_time=time(10, 0),
        end_local_time=time(13, 0),
    )

    assert shift is not None
    assert shift.barber_id == 1
    assert shift.weekday == 1
    assert len(session.added) == 1


@pytest.mark.asyncio
async def test_create_work_shift_normalizes_legacy_sunday_weekday() -> None:
    session = _FakeSession(overlap_id=None)
    repo = Repository(session)

    shift = await repo.create_work_shift(
        barber_id=1,
        weekday=7,
        start_local_time=time(10, 0),
        end_local_time=time(13, 0),
    )

    assert shift is not None
    assert shift.weekday == 6


@pytest.mark.asyncio
async def test_create_work_shift_rejects_out_of_range_weekday() -> None:
    session = _FakeSession(overlap_id=None)
    repo = Repository(session)

    shift = await repo.create_work_shift(
        barber_id=1,
        weekday=8,
        start_local_time=time(10, 0),
        end_local_time=time(13, 0),
    )

    assert shift is None
    assert session.added == []
