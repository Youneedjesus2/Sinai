"""Alembic environment configuration for Sinai API.

DATABASE_URL is read from the environment at runtime so no credentials
are stored in this file.  The value in alembic.ini is a placeholder only.

To generate a new migration:
    alembic revision --autogenerate -m "description"

To apply pending migrations:
    alembic upgrade head
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import create_engine, pool
from alembic import context

# ---------------------------------------------------------------------------
# Ensure the apps/api directory is on sys.path so that `src.*` imports work.
# ---------------------------------------------------------------------------
_api_root = Path(__file__).resolve().parents[2]
if str(_api_root) not in sys.path:
    sys.path.insert(0, str(_api_root))

# ---------------------------------------------------------------------------
# Alembic config object (gives access to alembic.ini values)
# ---------------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Override sqlalchemy.url from DATABASE_URL environment variable.
# This must happen before any SQLAlchemy engine is created.
# ---------------------------------------------------------------------------
_database_url = os.environ.get("DATABASE_URL", "")
if _database_url:
    config.set_main_option("sqlalchemy.url", _database_url)

# ---------------------------------------------------------------------------
# Import application models so Alembic autogenerate can detect schema changes.
# Provide placeholder values for required settings that aren't meaningful
# during migration runs (e.g. OPENAI_API_KEY is never used in migrations).
# ---------------------------------------------------------------------------
os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("OPENAI_API_KEY", "placeholder-for-migration")

from src.schemas import models as _models  # noqa: F401 — registers all ORM models
from src.core.db import Base

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Migration runner helpers
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL script)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
