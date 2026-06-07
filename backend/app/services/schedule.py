from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.service import ProviderSchedule, ProviderService, ServiceAppointment, ServiceProvider

DAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def parse_time(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def format_time(t: time) -> str:
    return t.strftime("%H:%M")


def format_opening_hours(raw: str | None) -> str | None:
    """Simplify OSM opening_hours for display."""
    if not raw:
        return None
    replacements = {
        "Mo": "Пн", "Tu": "Вт", "We": "Ср", "Th": "Чт", "Fr": "Пт", "Sa": "Сб", "Su": "Вс",
        "PH": "праздник", "off": "выходной", "24/7": "круглосуточно",
    }
    result = raw
    for eng, rus in replacements.items():
        result = result.replace(eng, rus)
    return result


async def get_provider_slots(
    db: AsyncSession,
    provider_id: int,
    target_date: date,
    service_duration: int = 60,
) -> tuple[list[dict], str | None]:
    result = await db.execute(
        select(ServiceProvider)
        .options(
            selectinload(ServiceProvider.schedule),
            selectinload(ServiceProvider.appointments),
        )
        .where(ServiceProvider.id == provider_id, ServiceProvider.is_active.is_(True))
    )
    provider = result.scalar_one_or_none()
    if not provider:
        return [], None

    dow = target_date.weekday()
    day_schedules = [s for s in provider.schedule if s.day_of_week == dow and s.is_working]
    if not day_schedules:
        return [], "Выходной"

    sched = day_schedules[0]
    working_hours = f"{format_time(sched.start_time)} – {format_time(sched.end_time)}"

    booked = [
        (a.start_time, a.end_time)
        for a in provider.appointments
        if a.appointment_date == target_date and a.status in ("booked", "confirmed")
    ]

    slots = []
    current = datetime.combine(target_date, sched.start_time)
    end = datetime.combine(target_date, sched.end_time)
    slot_delta = timedelta(minutes=30)

    while current + timedelta(minutes=service_duration) <= end:
        slot_start = current.time()
        slot_end = (current + timedelta(minutes=service_duration)).time()
        overlap = any(
            not (slot_end <= b_start or slot_start >= b_end)
            for b_start, b_end in booked
        )
        now_busy = target_date == date.today() and slot_start <= datetime.now().time()
        slots.append({
            "time": format_time(slot_start),
            "available": not overlap and not now_busy,
            "label": "Занято" if overlap else ("Прошло" if now_busy else "Свободно"),
        })
        current += slot_delta

    return slots, working_hours


async def get_provider_status_today(db: AsyncSession, provider: ServiceProvider) -> tuple[str, str | None]:
    today = date.today()
    slots, hours = await get_provider_slots(db, provider.id, today, 60)
    if not hours or hours == "Выходной":
        return "off", None
    free = [s for s in slots if s["available"]]
    if not free:
        return "busy", None
    return "free", free[0]["time"] if free else None
