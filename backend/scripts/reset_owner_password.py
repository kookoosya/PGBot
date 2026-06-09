#!/usr/bin/env python3
"""Reset owner password (temporary bootstrap). Usage: python scripts/reset_owner_password.py [username] [password]"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.core.security import get_password_hash
from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select


async def main() -> None:
    settings = get_settings()
    username = sys.argv[1] if len(sys.argv) > 1 else settings.SUPER_ADMIN_USERNAME
    password = sys.argv[2] if len(sys.argv) > 2 else "admin"

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            print(f"User not found: {username}")
            sys.exit(1)
        user.hashed_password = get_password_hash(password)
        user.failed_login_attempts = 0
        user.locked_until = None
        await db.commit()
        print(f"Password updated for {username}")


if __name__ == "__main__":
    asyncio.run(main())
