"""Seed script: create default admin user and roles."""
import asyncio
import sys
import os

# Allow running from project root or scripts/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from app.db.session import async_session_factory
from app.models.user import User, Role, user_roles
from app.core.security import hash_password
from sqlalchemy import select


async def seed():
    async with async_session_factory() as db:
        # ── Create default roles ──
        result = await db.execute(select(Role).where(Role.name == "admin"))
        admin_role = result.scalar_one_or_none()

        if admin_role is None:
            admin_role = Role(name="admin", description="系统管理员，拥有所有权限")
            db.add(admin_role)

        result = await db.execute(select(Role).where(Role.name == "user"))
        user_role = result.scalar_one_or_none()

        if user_role is None:
            user_role = Role(name="user", description="普通用户")
            db.add(user_role)

        await db.flush()

        # ── Create default admin user ──
        result = await db.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalar_one_or_none()

        if admin_user is None:
            admin_user = User(
                username="admin",
                email="admin@agent-platform.local",
                hashed_password=hash_password("admin123"),
                display_name="系统管理员",
                is_active=True,
                is_superuser=True,
            )
            db.add(admin_user)
            await db.flush()
            await db.refresh(admin_user)
        else:
            # Ensure existing admin always has superuser flag
            if not admin_user.is_superuser:
                admin_user.is_superuser = True
                await db.flush()

        # ── Assign admin role ──
        result = await db.execute(
            select(user_roles).where(
                user_roles.c.user_id == admin_user.id,
                user_roles.c.role_id == admin_role.id,
            )
        )
        if result.first() is None:
            await db.execute(
                user_roles.insert().values(
                    user_id=admin_user.id, role_id=admin_role.id
                )
            )

        await db.commit()

        print(f"Seed complete. Admin user: {admin_user.username} (id={admin_user.id})")
        print(f"Default password: admin123 (change after first login!)")


if __name__ == "__main__":
    asyncio.run(seed())
