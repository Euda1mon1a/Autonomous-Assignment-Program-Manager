"""Alembic environment configuration."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import get_settings
from app.db.base import Base

# Import all models to register them with Base.metadata
# These imports are required for autogenerate support even if not directly used
from app.models import (  # noqa: F401
    Absence,
    Assignment,
    Block,
    CallAssignment,
    Person,
    RotationTemplate,
    ScheduleRun,
)

# ============================================================================
# Continuum Table Exclusion
# ============================================================================
# SQLAlchemy-Continuum auto-creates version tables at runtime.
# These are NOT managed by Alembic migrations - exclude from autogenerate.
# See: docs/development/SCHEMA_AUDIT_REPORT.md
# ============================================================================
CONTINUUM_TABLES = {
    "transaction",
    "absences_version",
    "assignments_version",
    "import_batches_version",
    "import_staged_absences_version",
    "import_staged_assignments_version",
    "rotation_templates_version",
    "schedule_runs_version",
    "swap_records_version",
    # Legacy variant (if exists)
    "absence_version",
}


def include_object(object, name, type_, reflected, compare_to):
    """Filter objects for autogenerate.

    Excludes Continuum version tables which are auto-created at runtime.
    """
    if type_ == "table" and name in CONTINUUM_TABLES:
        return False
    return True


# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata for autogenerate support
target_metadata = Base.metadata

# Get database URL from settings
settings = get_settings()


def get_url():
    """Get database URL from settings."""
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
