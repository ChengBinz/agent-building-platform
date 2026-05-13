"""Fix alembic_version for databases created before Alembic was set up."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from alembic.config import Config
from alembic import command
from app.db.session import async_session_factory


async def check_db_state():
    """Check if database has tables but no valid alembic_version."""
    async with async_session_factory() as db:
        # Check if alembic_version table exists
        result = await db.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"
        ))
        table_exists = result.scalar()

        if not table_exists:
            # Check if other tables exist (old DB created by create_all)
            result = await db.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
            ))
            return result.scalar()  # True = old DB needs stamp

        # Check if current version is valid
        result = await db.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.scalar()
        valid_versions = ['001_init_all_tables', '251a05db90b7']
        return current_version not in valid_versions


async def main():
    needs_fix = await check_db_state()
    if needs_fix:
        print("Old database detected, stamping current version...")
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "head")
        print("Done.")
    else:
        print("Database state is valid.")


if __name__ == "__main__":
    asyncio.run(main())
