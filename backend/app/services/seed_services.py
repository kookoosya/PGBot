"""Seed demo service providers for Pushkinogory."""

from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ServiceType, VerificationStatus
from app.models.service import ProviderSchedule, ProviderService, ServiceProvider

DEMO_PROVIDERS = [
    {
        "full_name": "Анна Петрова",
        "phone": "+79111234501",
        "bio": "Мастер маникюра и педикюра. Опыт 8 лет. Пушкинские Горы.",
        "address": "ул. Красноармейская, 12",
        "services": [
            (ServiceType.MANICURE, "Классический маникюр", 60, 800),
            (ServiceType.PEDICURE, "Педикюр", 90, 1200),
        ],
    },
    {
        "full_name": "Мария Сидорова",
        "phone": "+79111234502",
        "bio": "Парикмахер-стилист. Стрижки, укладки, окрашивание.",
        "address": "ул. Ленина, 5",
        "services": [
            (ServiceType.HAIRCUT, "Женская стрижка", 60, 600),
            (ServiceType.HAIRCUT, "Мужская стрижка", 30, 400),
            (ServiceType.HAIR_COLOR, "Окрашивание", 120, 2500),
        ],
    },
    {
        "full_name": "Елена Козлова",
        "phone": "+79111234503",
        "bio": "Бровист и лашмейкер. Коррекция бровей, ламинирование.",
        "address": "Пушкинские Горы, центр",
        "services": [
            (ServiceType.BROWS, "Коррекция бровей", 30, 500),
            (ServiceType.BROWS, "Ламинирование ресниц", 90, 1500),
        ],
    },
]

DEFAULT_SCHEDULE = [
    (0, time(9, 0), time(18, 0)),   # Mon
    (1, time(9, 0), time(18, 0)),
    (2, time(9, 0), time(18, 0)),
    (3, time(9, 0), time(18, 0)),
    (4, time(9, 0), time(18, 0)),
    (5, time(10, 0), time(16, 0)),  # Sat
    (6, time(0, 0), time(0, 0), False),  # Sun off
]


async def seed_service_providers(db: AsyncSession) -> int:
    count = 0
    for data in DEMO_PROVIDERS:
        result = await db.execute(
            select(ServiceProvider).where(ServiceProvider.phone == data["phone"])
        )
        if result.scalar_one_or_none():
            continue

        provider = ServiceProvider(
            full_name=data["full_name"],
            phone=data["phone"],
            bio=data["bio"],
            address=data["address"],
            verification_status=VerificationStatus.APPROVED,
            is_active=True,
        )
        db.add(provider)
        await db.flush()

        for stype, name, duration, price in data["services"]:
            db.add(ProviderService(
                provider_id=provider.id,
                service_type=stype,
                name=name,
                duration_minutes=duration,
                price=price,
            ))

        for item in DEFAULT_SCHEDULE:
            dow, start, end = item[0], item[1], item[2]
            is_working = item[3] if len(item) > 3 else True
            db.add(ProviderSchedule(
                provider_id=provider.id,
                day_of_week=dow,
                start_time=start,
                end_time=end if is_working else time(0, 0),
                is_working=is_working,
            ))
        count += 1

    await db.flush()
    return count
