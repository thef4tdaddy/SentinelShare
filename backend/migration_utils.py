import os

from sqlalchemy import inspect

from alembic import command
from alembic.config import Config
from backend.database import engine


def run_migrations():
    """
    Automatically handles database migrations on startup.
    1. Detects legacy DB (tables exist but no alembic_version) -> Stamps head.
    2. Runs upgrade head to apply any new changes.
    """
    print("Startup: Checking database migration status...")

    # Ensure alembic.ini is found (we assume we are running from project root)
    alembic_ini_path = "alembic.ini"
    if not os.path.exists(alembic_ini_path):
        print(f"Warning: {alembic_ini_path} not found. Skipping migrations.")
        return

    alembic_cfg = Config(alembic_ini_path)

    # Need to verify connection logic for Alembic config if strictly programmatic,
    # but since alembic.ini and env.py are set up to read env vars, it should work fine
    # as long as the CWD is correct.

    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        # Check for legacy state: App tables exist, but Alembic doesn't track them yet
        if (
            "processedemail" in existing_tables
            and "alembic_version" not in existing_tables
        ):
            print(
                "Detected existing tables without Alembic history. Stamping 'head' to mark as current."
            )
            command.stamp(alembic_cfg, "head")

        # Always try to upgrade to latest
        print("Applying pending migrations...")
        command.upgrade(alembic_cfg, "head")
        print("Migrations complete.")

    except Exception as e:
        print(f"Error running migrations: {e}")
        # We don't raise here because we don't want to crash the app if DB is flaky,
        # but in production, maybe we should. For now, log and continue.
