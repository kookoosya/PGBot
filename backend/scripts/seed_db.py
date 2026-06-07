#!/usr/bin/env python3
"""Seed database with initial roles, departments, and super admin."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.enums import UserRole
from app.models.user import Role, User

settings = get_settings()

ROLES = [
    (UserRole.RESIDENT, "Житель поселка"),
    (UserRole.MODERATOR, "Модератор"),
    (UserRole.ADMINISTRATION, "Администрация района"),
    (UserRole.SOCIAL_SERVICE, "Социальные службы"),
    (UserRole.SUPER_ADMIN, "Суперадминистратор"),
    (UserRole.SERVICE_PROVIDER, "Мастер услуг"),
]

DEPARTMENTS = [
    ("ЖКХ", "Жилищно-коммунальное хозяйство"),
    ("Администрация", "Администрация поселка"),
    ("Дорожная служба", "Содержание дорог и тротуаров"),
    ("Экология", "Экологический отдел"),
    ("Социальная защита", "Отдел социальной защиты населения"),
]


async def seed() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        for role_name, description in ROLES:
            result = await db.execute(select(Role).where(Role.name == role_name))
            if not result.scalar_one_or_none():
                db.add(Role(name=role_name, description=description))

        for name, description in DEPARTMENTS:
            result = await db.execute(select(Department).where(Department.name == name))
            if not result.scalar_one_or_none():
                db.add(Department(name=name, description=description))

        await db.flush()

        admin_username = os.getenv("SUPER_ADMIN_USERNAME", "admin")
        admin_password = os.getenv("SUPER_ADMIN_PASSWORD", "admin123")

        result = await db.execute(select(User).where(User.username == admin_username))
        if not result.scalar_one_or_none():
            role_result = await db.execute(select(Role).where(Role.name == UserRole.SUPER_ADMIN))
            role = role_result.scalar_one()
            db.add(User(
                username=admin_username,
                email="admin@pushkinskie-gory.local",
                hashed_password=get_password_hash(admin_password),
                full_name="Суперадминистратор",
                role_id=role.id,
            ))
            print(f"Created super admin: {admin_username}")

        from app.services.osm_sync import seed_pushkin_landmarks, sync_places_from_osm
        from app.services.seed_services import seed_service_providers
        seeded = await seed_pushkin_landmarks(db)
        print(f"Seeded {seeded} landmarks")
        try:
            osm = await sync_places_from_osm(db)
            print(f"OSM sync: {osm}")
        except Exception as e:
            print(f"OSM sync skipped: {e}")

        svc_count = await seed_service_providers(db)
        print(f"Seeded {svc_count} service providers")

        import subprocess
        subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "cleanup_demo_providers.py")], check=False)

        await db.commit()
        print("Database seeded successfully")


if __name__ == "__main__":
    asyncio.run(seed())
