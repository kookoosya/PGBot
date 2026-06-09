#!/usr/bin/env python3
"""Remove demo service providers if they exist from earlier seeds."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.service import (
    ProviderSchedule,
    ProviderService,
    ServiceAppointment,
    ServiceProvider,
)
from sqlalchemy import delete, select

DEMO_PHONES = ["+79111234501", "+79111234502", "+79111234503"]


async def cleanup() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ServiceProvider).where(ServiceProvider.phone.in_(DEMO_PHONES)))
        providers = result.scalars().all()
        from app.models.provider_busy import ProviderBusyBlock

        for p in providers:
            await db.execute(delete(ServiceAppointment).where(ServiceAppointment.provider_id == p.id))
            await db.execute(delete(ProviderBusyBlock).where(ProviderBusyBlock.provider_id == p.id))
            await db.execute(delete(ProviderSchedule).where(ProviderSchedule.provider_id == p.id))
            await db.execute(delete(ProviderService).where(ProviderService.provider_id == p.id))
            await db.execute(delete(ServiceProvider).where(ServiceProvider.id == p.id))
        await db.commit()
        print(f"Removed {len(providers)} demo providers")


if __name__ == "__main__":
    get_settings()
    asyncio.run(cleanup())
