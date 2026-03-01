from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Sequence
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from barber_bot.db.models import (
    AdminUser,
    Barber,
    Booking,
    BookingEvent,
    BookingStatus,
    Client,
    ReminderJob,
    Service,
    WorkShift,
)


@dataclass(slots=True)
class DueReminder:
    reminder_id: int
    booking_id: int
    tg_user_id: int
    locale: str
    starts_at_utc: datetime
    kind: str


@dataclass(slots=True)
class TodayBookingDetailed:
    booking_id: int
    starts_at_utc: datetime
    ends_at_utc: datetime
    status: str
    barber_id: int | None
    barber_name: str | None
    service_id: int | None
    service_name_ru: str | None
    service_name_uz: str | None
    service_name_tj: str | None
    client_id: int | None
    client_tg_user_id: int | None
    client_tg_username: str | None
    client_phone_e164: str | None


def service_name_by_locale(
    locale: str | None,
    *,
    name_ru: str | None,
    name_uz: str | None,
    name_tj: str | None,
) -> str:
    if locale == "uz":
        return name_uz or name_ru or name_tj or "-"
    if locale == "tj":
        return name_tj or name_ru or name_uz or "-"
    return name_ru or name_uz or name_tj or "-"


class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_client(
        self,
        tg_user_id: int | None,
        default_locale: str,
        *,
        tg_username: str | None = None,
        tg_first_name: str | None = None,
        tg_last_name: str | None = None,
    ) -> Client:
        if tg_user_id is not None:
            client = await self.get_client_by_tg_user_id(tg_user_id)
            if client:
                updated = False
                if client.tg_username != tg_username:
                    client.tg_username = tg_username
                    updated = True
                if client.tg_first_name != tg_first_name:
                    client.tg_first_name = tg_first_name
                    updated = True
                if client.tg_last_name != tg_last_name:
                    client.tg_last_name = tg_last_name
                    updated = True
                if updated:
                    await self.session.flush()
                return client

        client = Client(
            tg_user_id=tg_user_id,
            locale=default_locale,
            tg_username=tg_username,
            tg_first_name=tg_first_name,
            tg_last_name=tg_last_name,
        )
        self.session.add(client)
        await self.session.flush()
        return client

    async def get_client_by_tg_user_id(self, tg_user_id: int | None) -> Client | None:
        if tg_user_id is None:
            return None
        result = await self.session.execute(select(Client).where(Client.tg_user_id == tg_user_id))
        return result.scalar_one_or_none()

    async def get_client_by_phone(self, phone_e164: str) -> Client | None:
        result = await self.session.execute(select(Client).where(Client.phone_e164 == phone_e164))
        return result.scalar_one_or_none()

    async def create_guest_client(
        self,
        phone_e164: str,
        locale: str,
    ) -> Client:
        existing = await self.get_client_by_phone(phone_e164)
        if existing is not None:
            return existing
        client = Client(
            tg_user_id=None,
            phone_e164=phone_e164,
            locale=locale,
        )
        self.session.add(client)
        await self.session.flush()
        return client

    async def upsert_client_profile(
        self,
        *,
        tg_user_id: int,
        locale: str,
        tg_username: str | None,
        tg_first_name: str | None,
        tg_last_name: str | None,
    ) -> Client:
        return await self.get_or_create_client(
            tg_user_id=tg_user_id,
            default_locale=locale,
            tg_username=tg_username,
            tg_first_name=tg_first_name,
            tg_last_name=tg_last_name,
        )

    async def update_client_phone(self, client_id: int, phone_e164: str) -> None:
        client = await self.session.get(Client, client_id)
        if not client:
            return
        client.phone_e164 = phone_e164
        await self.session.flush()

    async def update_client_locale(self, client_id: int, locale: str) -> None:
        client = await self.session.get(Client, client_id)
        if not client:
            return
        client.locale = locale
        await self.session.flush()

    async def list_active_services(self) -> list[Service]:
        result = await self.session.execute(
            select(Service).where(Service.is_active.is_(True)).order_by(Service.id)
        )
        return list(result.scalars().all())

    async def list_services(self, include_inactive: bool = False) -> list[Service]:
        query = select(Service)
        if not include_inactive:
            query = query.where(Service.is_active.is_(True))
        query = query.order_by(Service.id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_service(self, service_id: int) -> Service | None:
        return await self.session.get(Service, service_id)

    async def list_active_barbers(self) -> list[Barber]:
        result = await self.session.execute(
            select(Barber).where(Barber.is_active.is_(True)).order_by(Barber.id)
        )
        return list(result.scalars().all())

    async def list_barbers(self, include_inactive: bool = False) -> list[Barber]:
        query = select(Barber)
        if not include_inactive:
            query = query.where(Barber.is_active.is_(True))
        query = query.order_by(Barber.id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_barber(self, barber_id: int) -> Barber | None:
        return await self.session.get(Barber, barber_id)

    async def list_shifts_for_barber_weekday(self, barber_id: int, weekday: int) -> list[WorkShift]:
        result = await self.session.execute(
            select(WorkShift)
            .where(
                WorkShift.barber_id == barber_id,
                WorkShift.weekday == weekday,
                WorkShift.is_active.is_(True),
            )
            .order_by(WorkShift.start_local_time)
        )
        return list(result.scalars().all())

    async def list_work_shifts(self, barber_id: int) -> list[WorkShift]:
        result = await self.session.execute(
            select(WorkShift)
            .where(WorkShift.barber_id == barber_id, WorkShift.is_active.is_(True))
            .order_by(WorkShift.weekday, WorkShift.start_local_time)
        )
        return list(result.scalars().all())

    async def list_busy_intervals_for_local_day(
        self, barber_id: int, local_day: date, tz_name: str
    ) -> list[tuple[datetime, datetime]]:
        day_start_local = datetime.combine(local_day, datetime.min.time(), ZoneInfo(tz_name))
        day_end_local = day_start_local + timedelta(days=1)
        day_start_utc = day_start_local.astimezone(UTC)
        day_end_utc = day_end_local.astimezone(UTC)

        result = await self.session.execute(
            select(Booking.starts_at_utc, Booking.ends_at_utc)
            .where(
                Booking.barber_id == barber_id,
                Booking.status.in_(
                    [
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.COMPLETED.value,
                        BookingStatus.BLOCKED.value,
                    ]
                ),
                Booking.starts_at_utc < day_end_utc,
                Booking.ends_at_utc > day_start_utc,
            )
            .order_by(Booking.starts_at_utc)
        )
        return list(result.all())

    async def _create_confirmed_booking(
        self,
        *,
        client_id: int,
        barber_id: int,
        service_id: int,
        starts_at_utc: datetime,
        ends_at_utc: datetime,
        source: str,
        created_by_admin_id: int | None,
        actor_tg_user_id: int | None,
    ) -> Booking | None:
        # Lock possible overlapping bookings to avoid race conditions.
        overlap_query = (
            select(Booking)
            .where(
                Booking.barber_id == barber_id,
                Booking.status.in_(
                    [
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.COMPLETED.value,
                        BookingStatus.BLOCKED.value,
                    ]
                ),
                Booking.starts_at_utc < ends_at_utc,
                Booking.ends_at_utc > starts_at_utc,
            )
            .with_for_update()
        )
        overlap_rows = await self.session.execute(overlap_query)
        has_overlap = overlap_rows.scalars().first() is not None
        if has_overlap:
            return None

        booking = Booking(
            client_id=client_id,
            barber_id=barber_id,
            service_id=service_id,
            starts_at_utc=starts_at_utc,
            ends_at_utc=ends_at_utc,
            status=BookingStatus.CONFIRMED.value,
            created_by_admin_id=created_by_admin_id,
        )
        self.session.add(booking)
        await self.session.flush()

        self.session.add(
            BookingEvent(
                booking_id=booking.id,
                event_type="created",
                payload_json={
                    "source": source,
                    "client_id": client_id,
                    "actor_tg_user_id": actor_tg_user_id,
                },
            )
        )
        return booking

    async def create_confirmed_booking(
        self,
        *,
        client_id: int,
        barber_id: int,
        service_id: int,
        starts_at_utc: datetime,
        ends_at_utc: datetime,
    ) -> Booking | None:
        return await self._create_confirmed_booking(
            client_id=client_id,
            barber_id=barber_id,
            service_id=service_id,
            starts_at_utc=starts_at_utc,
            ends_at_utc=ends_at_utc,
            source="client",
            created_by_admin_id=None,
            actor_tg_user_id=None,
        )

    async def create_confirmed_booking_admin(
        self,
        *,
        client_id: int,
        barber_id: int,
        service_id: int,
        starts_at_utc: datetime,
        ends_at_utc: datetime,
        admin_tg_user_id: int,
    ) -> Booking | None:
        admin_user_id = await self.get_admin_user_id(admin_tg_user_id)
        return await self._create_confirmed_booking(
            client_id=client_id,
            barber_id=barber_id,
            service_id=service_id,
            starts_at_utc=starts_at_utc,
            ends_at_utc=ends_at_utc,
            source="admin",
            created_by_admin_id=admin_user_id,
            actor_tg_user_id=admin_tg_user_id,
        )

    async def create_blocked_booking(
        self,
        *,
        barber_id: int,
        starts_at_utc: datetime,
        ends_at_utc: datetime,
        admin_id: int | None,
        note: str | None,
    ) -> Booking | None:
        overlap_query = (
            select(Booking)
            .where(
                Booking.barber_id == barber_id,
                Booking.status.in_(
                    [
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.COMPLETED.value,
                        BookingStatus.BLOCKED.value,
                    ]
                ),
                Booking.starts_at_utc < ends_at_utc,
                Booking.ends_at_utc > starts_at_utc,
            )
            .with_for_update()
        )
        overlap_rows = await self.session.execute(overlap_query)
        if overlap_rows.scalars().first() is not None:
            return None

        booking = Booking(
            client_id=None,
            barber_id=barber_id,
            service_id=None,
            starts_at_utc=starts_at_utc,
            ends_at_utc=ends_at_utc,
            status=BookingStatus.BLOCKED.value,
            created_by_admin_id=admin_id,
            note=note,
        )
        self.session.add(booking)
        await self.session.flush()
        self.session.add(
            BookingEvent(
                booking_id=booking.id,
                event_type="blocked",
                payload_json={"admin_id": admin_id, "note": note},
            )
        )
        return booking

    async def create_reminder_jobs_for_booking(
        self,
        booking: Booking,
        *,
        kinds: Sequence[tuple[int, str]] = ((24, "24h"), (2, "2h"), (0, "30m")),
        allow_without_tg: bool = False,
    ) -> int:
        if booking.client_id is None:
            return 0
        if not allow_without_tg:
            client = await self.session.get(Client, booking.client_id)
            if client is None or client.tg_user_id is None:
                return 0

        created = 0
        for amount, kind in kinds:
            if kind == "30m":
                scheduled_at = booking.starts_at_utc - timedelta(minutes=30)
            else:
                scheduled_at = booking.starts_at_utc - timedelta(hours=amount)
            if scheduled_at <= datetime.now(UTC):
                continue
            existing = await self.session.execute(
                select(ReminderJob).where(
                    ReminderJob.booking_id == booking.id,
                    ReminderJob.kind == kind,
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue
            self.session.add(
                ReminderJob(booking_id=booking.id, kind=kind, scheduled_at_utc=scheduled_at)
            )
            created += 1
        return created

    async def list_future_bookings_for_client(self, client_id: int) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(
                Booking.client_id == client_id,
                Booking.status == BookingStatus.CONFIRMED.value,
                Booking.starts_at_utc > datetime.now(UTC),
            )
            .order_by(Booking.starts_at_utc)
        )
        return list(result.scalars().all())

    async def get_booking_for_client(self, booking_id: int, client_id: int) -> Booking | None:
        result = await self.session.execute(
            select(Booking).where(Booking.id == booking_id, Booking.client_id == client_id)
        )
        return result.scalar_one_or_none()

    async def get_booking(self, booking_id: int) -> Booking | None:
        return await self.session.get(Booking, booking_id)

    async def get_booking_detailed(self, booking_id: int) -> TodayBookingDetailed | None:
        result = await self.session.execute(
            select(
                Booking.id,
                Booking.starts_at_utc,
                Booking.ends_at_utc,
                Booking.status,
                Booking.barber_id,
                Barber.name,
                Booking.service_id,
                Service.name_ru,
                Service.name_uz,
                Service.name_tj,
                Booking.client_id,
                Client.tg_user_id,
                Client.tg_username,
                Client.phone_e164,
            )
            .outerjoin(Barber, Barber.id == Booking.barber_id)
            .outerjoin(Service, Service.id == Booking.service_id)
            .outerjoin(Client, Client.id == Booking.client_id)
            .where(Booking.id == booking_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        return TodayBookingDetailed(*row)

    async def set_booking_status(
        self,
        *,
        booking_id: int,
        new_status: str,
        reason: str,
        actor_tg_user_id: int | None,
    ) -> Booking | None:
        booking = await self.session.get(Booking, booking_id)
        if booking is None:
            return None

        old_status = booking.status
        if old_status == new_status:
            return booking

        if (
            old_status == BookingStatus.CONFIRMED.value
            and new_status == BookingStatus.COMPLETED.value
        ):
            event_type = "service_completed"
        elif (
            old_status == BookingStatus.COMPLETED.value
            and new_status == BookingStatus.CONFIRMED.value
        ):
            event_type = "service_completion_reverted"
        else:
            return None

        booking.status = new_status
        self.session.add(
            BookingEvent(
                booking_id=booking.id,
                event_type=event_type,
                payload_json={
                    "from_status": old_status,
                    "to_status": new_status,
                    "reason": reason,
                    "actor_tg_user_id": actor_tg_user_id,
                },
            )
        )
        await self.session.flush()
        return booking

    async def cancel_booking(self, booking: Booking, reason: str = "client_cancelled") -> None:
        booking.status = BookingStatus.CANCELLED.value
        booking.cancelled_at_utc = datetime.now(UTC)
        self.session.add(
            BookingEvent(
                booking_id=booking.id,
                event_type="cancelled",
                payload_json={"reason": reason},
            )
        )
        await self.session.flush()

    async def is_admin(self, tg_user_id: int, settings_admin_ids: set[int]) -> bool:
        if tg_user_id in settings_admin_ids:
            return True
        result = await self.session.execute(
            select(AdminUser.id).where(AdminUser.tg_user_id == tg_user_id)
        )
        return result.scalar_one_or_none() is not None

    async def get_admin_user_id(self, tg_user_id: int) -> int | None:
        result = await self.session.execute(
            select(AdminUser.id).where(AdminUser.tg_user_id == tg_user_id)
        )
        row = result.scalar_one_or_none()
        return int(row) if row is not None else None

    async def list_today_bookings(self, tz_name: str) -> list[Booking]:
        now_local = datetime.now(ZoneInfo(tz_name))
        day_start_utc, day_end_utc = self._local_day_bounds_utc(tz_name, now_local.date())

        result = await self.session.execute(
            select(Booking)
            .where(
                Booking.status.in_(
                    [
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.COMPLETED.value,
                        BookingStatus.BLOCKED.value,
                        BookingStatus.CANCELLED.value,
                    ]
                ),
                Booking.starts_at_utc >= day_start_utc,
                Booking.starts_at_utc < day_end_utc,
            )
            .order_by(Booking.starts_at_utc)
        )
        return list(result.scalars().all())

    def _local_day_bounds_utc(self, tz_name: str, local_day: date) -> tuple[datetime, datetime]:
        day_start_local = datetime.combine(local_day, datetime.min.time(), ZoneInfo(tz_name))
        day_end_local = day_start_local + timedelta(days=1)
        return day_start_local.astimezone(UTC), day_end_local.astimezone(UTC)

    async def list_today_bookings_detailed(
        self,
        tz_name: str,
        include_statuses: Sequence[str] = (
            BookingStatus.CONFIRMED.value,
            BookingStatus.COMPLETED.value,
            BookingStatus.BLOCKED.value,
            BookingStatus.CANCELLED.value,
        ),
    ) -> list[TodayBookingDetailed]:
        now_local = datetime.now(ZoneInfo(tz_name))
        day_start_utc, day_end_utc = self._local_day_bounds_utc(tz_name, now_local.date())
        return await self.list_bookings_detailed_for_range(
            starts_from_utc=day_start_utc,
            starts_to_utc=day_end_utc,
            include_statuses=include_statuses,
        )

    async def list_monitoring_bookings_detailed(
        self,
        tz_name: str,
        *,
        days: int = 14,
        include_statuses: Sequence[str] = (
            BookingStatus.CONFIRMED.value,
            BookingStatus.COMPLETED.value,
            BookingStatus.BLOCKED.value,
            BookingStatus.CANCELLED.value,
        ),
    ) -> list[TodayBookingDetailed]:
        now_local = datetime.now(ZoneInfo(tz_name))
        local_today = now_local.date()
        day_start_utc, _ = self._local_day_bounds_utc(tz_name, local_today)

        range_end_local = datetime.combine(
            local_today + timedelta(days=days + 1),
            datetime.min.time(),
            ZoneInfo(tz_name),
        )
        range_end_utc = range_end_local.astimezone(UTC)

        return await self.list_bookings_detailed_for_range(
            starts_from_utc=day_start_utc,
            starts_to_utc=range_end_utc,
            include_statuses=include_statuses,
        )

    async def list_bookings_detailed_for_range(
        self,
        *,
        starts_from_utc: datetime,
        starts_to_utc: datetime,
        include_statuses: Sequence[str],
        limit: int | None = None,
    ) -> list[TodayBookingDetailed]:
        query = (
            select(
                Booking.id,
                Booking.starts_at_utc,
                Booking.ends_at_utc,
                Booking.status,
                Booking.barber_id,
                Barber.name,
                Booking.service_id,
                Service.name_ru,
                Service.name_uz,
                Service.name_tj,
                Booking.client_id,
                Client.tg_user_id,
                Client.tg_username,
                Client.phone_e164,
            )
            .outerjoin(Barber, Barber.id == Booking.barber_id)
            .outerjoin(Service, Service.id == Booking.service_id)
            .outerjoin(Client, Client.id == Booking.client_id)
            .where(
                Booking.starts_at_utc >= starts_from_utc,
                Booking.starts_at_utc < starts_to_utc,
                Booking.status.in_(list(include_statuses)),
            )
            .order_by(Booking.starts_at_utc)
        )
        if limit is not None:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return [TodayBookingDetailed(*row) for row in result.all()]

    async def sum_cash_for_range(
        self,
        *,
        starts_from_utc: datetime,
        starts_to_utc: datetime,
        include_statuses: Sequence[str] = (BookingStatus.COMPLETED.value,),
    ) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Service.price_minor), 0))
            .select_from(Booking)
            .outerjoin(Service, Service.id == Booking.service_id)
            .where(
                Booking.starts_at_utc >= starts_from_utc,
                Booking.starts_at_utc < starts_to_utc,
                Booking.status.in_(list(include_statuses)),
            )
        )
        value = result.scalar_one_or_none()
        return int(value or 0)

    async def list_upcoming_bookings_detailed(
        self,
        tz_name: str,
        *,
        days: int = 14,
        include_statuses: Sequence[str] = (
            BookingStatus.CONFIRMED.value,
            BookingStatus.COMPLETED.value,
            BookingStatus.BLOCKED.value,
            BookingStatus.CANCELLED.value,
        ),
        limit: int = 100,
    ) -> list[TodayBookingDetailed]:
        now_utc = datetime.now(UTC)
        max_utc = now_utc + timedelta(days=days)
        return await self.list_bookings_detailed_for_range(
            starts_from_utc=now_utc,
            starts_to_utc=max_utc,
            include_statuses=include_statuses,
            limit=limit,
        )

    async def list_today_bookings_for_visits(self, tz_name: str) -> list[TodayBookingDetailed]:
        return await self.list_today_bookings_detailed(
            tz_name,
            include_statuses=(
                BookingStatus.CONFIRMED.value,
                BookingStatus.COMPLETED.value,
                BookingStatus.BLOCKED.value,
                BookingStatus.CANCELLED.value,
            ),
        )

    async def upsert_service(
        self, *, duration_min: int, price_minor: int, name_ru: str, name_uz: str, name_tj: str
    ) -> Service:
        service = Service(
            duration_min=duration_min,
            price_minor=price_minor,
            name_ru=name_ru,
            name_uz=name_uz,
            name_tj=name_tj,
            is_active=True,
        )
        self.session.add(service)
        await self.session.flush()
        return service

    async def create_service(
        self, *, duration_min: int, price_minor: int, name_ru: str, name_uz: str, name_tj: str
    ) -> Service:
        return await self.upsert_service(
            duration_min=duration_min,
            price_minor=price_minor,
            name_ru=name_ru,
            name_uz=name_uz,
            name_tj=name_tj,
        )

    async def update_service(
        self,
        service_id: int,
        *,
        duration_min: int,
        price_minor: int,
        name_ru: str,
        name_uz: str,
        name_tj: str,
    ) -> bool:
        service = await self.session.get(Service, service_id)
        if not service:
            return False
        service.duration_min = duration_min
        service.price_minor = price_minor
        service.name_ru = name_ru
        service.name_uz = name_uz
        service.name_tj = name_tj
        await self.session.flush()
        return True

    async def toggle_service(self, service_id: int, is_active: bool) -> bool:
        service = await self.session.get(Service, service_id)
        if not service:
            return False
        service.is_active = is_active
        await self.session.flush()
        return True

    async def archive_service(self, service_id: int) -> bool:
        return await self.toggle_service(service_id, False)

    async def restore_service(self, service_id: int) -> bool:
        return await self.toggle_service(service_id, True)

    async def delete_service_hard(self, service_id: int) -> bool:
        service = await self.session.get(Service, service_id)
        if not service:
            return False
        await self.session.delete(service)
        await self.session.flush()
        return True

    async def toggle_barber(self, barber_id: int, is_active: bool) -> bool:
        barber = await self.session.get(Barber, barber_id)
        if not barber:
            return False
        barber.is_active = is_active
        await self.session.flush()
        return True

    async def create_barber(self, name: str) -> Barber:
        barber = Barber(name=name, is_active=True)
        self.session.add(barber)
        await self.session.flush()
        return barber

    async def update_barber_name(self, barber_id: int, name: str) -> bool:
        barber = await self.session.get(Barber, barber_id)
        if not barber:
            return False
        barber.name = name
        await self.session.flush()
        return True

    async def archive_barber(self, barber_id: int) -> bool:
        return await self.toggle_barber(barber_id, False)

    async def restore_barber(self, barber_id: int) -> bool:
        return await self.toggle_barber(barber_id, True)

    async def delete_barber_hard(self, barber_id: int) -> bool:
        barber = await self.session.get(Barber, barber_id)
        if not barber:
            return False
        await self.session.execute(
            update(Booking).where(Booking.barber_id == barber_id).values(barber_id=None)
        )
        await self.session.delete(barber)
        await self.session.flush()
        return True

    async def delete_booking_hard(self, booking_id: int) -> bool:
        booking = await self.session.get(Booking, booking_id)
        if not booking:
            return False
        if booking.status == BookingStatus.COMPLETED.value:
            return False
        await self.session.delete(booking)
        await self.session.flush()
        return True

    async def create_work_shift(
        self,
        *,
        barber_id: int,
        weekday: int,
        start_local_time: time,
        end_local_time: time,
    ) -> WorkShift | None:
        if weekday == 7:
            weekday = 6
        if weekday < 0 or weekday > 6:
            return None
        if start_local_time >= end_local_time:
            return None

        overlap_result = await self.session.execute(
            select(WorkShift.id).where(
                WorkShift.barber_id == barber_id,
                WorkShift.weekday == weekday,
                WorkShift.is_active.is_(True),
                WorkShift.start_local_time < end_local_time,
                WorkShift.end_local_time > start_local_time,
            )
        )
        if overlap_result.scalar_one_or_none() is not None:
            return None

        shift = WorkShift(
            barber_id=barber_id,
            weekday=weekday,
            start_local_time=start_local_time,
            end_local_time=end_local_time,
            is_active=True,
        )
        self.session.add(shift)
        await self.session.flush()
        return shift

    async def delete_work_shift(self, shift_id: int) -> bool:
        shift = await self.session.get(WorkShift, shift_id)
        if not shift:
            return False
        await self.session.delete(shift)
        await self.session.flush()
        return True

    async def list_due_reminders(self, limit: int = 100) -> list[DueReminder]:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(
                ReminderJob.id,
                ReminderJob.booking_id,
                Client.tg_user_id,
                Client.locale,
                Booking.starts_at_utc,
                ReminderJob.kind,
            )
            .join(Booking, Booking.id == ReminderJob.booking_id)
            .join(Client, Client.id == Booking.client_id)
            .where(
                ReminderJob.sent_at_utc.is_(None),
                ReminderJob.scheduled_at_utc <= now,
                Booking.status == BookingStatus.CONFIRMED.value,
                Client.tg_user_id.is_not(None),
            )
            .order_by(ReminderJob.scheduled_at_utc)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return [DueReminder(*row) for row in result.all()]

    async def mark_reminder_sent(self, reminder_id: int) -> None:
        reminder = await self.session.get(ReminderJob, reminder_id)
        if reminder is None:
            return
        reminder.sent_at_utc = datetime.now(UTC)
        await self.session.flush()

    async def increment_reminder_attempt(self, reminder_id: int) -> None:
        reminder = await self.session.get(ReminderJob, reminder_id)
        if reminder is None:
            return
        reminder.attempts += 1
        await self.session.flush()

    async def ping(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(Service))
        return int(result.scalar_one())
