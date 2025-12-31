"""Debugging and diagnostics CLI commands."""

import sys
from typing import Optional

import click
from sqlalchemy import text

from app.core.logging import get_logger
from app.db.session import SessionLocal

logger = get_logger(__name__)


@click.group()
def debug() -> None:
    """Debugging and diagnostics commands."""
    pass


@debug.command()
def check_health() -> None:
    """
    Run comprehensive system health check.

    Checks:
    - Database connectivity
    - Redis connectivity
    - Celery worker status
    - Configuration validity

    Example:
        python -m app.cli debug check-health
    """
    from app.health.aggregator import HealthAggregator

    try:
        click.echo("Running system health check...\n")

        aggregator = HealthAggregator()
        health = aggregator.check_health()

        # Display results
        click.echo("=" * 60)
        click.echo(f"System Health: {health.status.upper()}")
        click.echo("=" * 60)

        for check_name, result in health.checks.items():
            status_symbol = "✓" if result.status == "healthy" else "✗"
            click.echo(f"\n{status_symbol} {check_name.upper()}: {result.status}")

            if result.message:
                click.echo(f"  Message: {result.message}")

            if result.details:
                for key, value in result.details.items():
                    click.echo(f"  {key}: {value}")

        click.echo("\n" + "=" * 60)

        # Exit with error code if unhealthy
        if health.status != "healthy":
            sys.exit(1)

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@debug.command()
def test_db() -> None:
    """
    Test database connection and run diagnostic queries.

    Example:
        python -m app.cli debug test-db
    """
    db = SessionLocal()

    try:
        click.echo("Testing database connection...")

        # Test basic connectivity
        result = db.execute(text("SELECT 1"))
        assert result.scalar() == 1
        click.echo("✓ Database connection successful")

        # Check database version
        result = db.execute(text("SELECT version()"))
        version = result.scalar()
        click.echo(f"✓ PostgreSQL version: {version.split(',')[0]}")

        # Check current user and database
        result = db.execute(text("SELECT current_user, current_database()"))
        user, database = result.fetchone()
        click.echo(f"✓ Connected as: {user}")
        click.echo(f"✓ Database: {database}")

        # Check table count
        result = db.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
        )
        table_count = result.scalar()
        click.echo(f"✓ Tables: {table_count}")

        # Test query performance
        import time

        start = time.time()
        db.execute(text("SELECT COUNT(*) FROM blocks"))
        duration = time.time() - start
        click.echo(f"✓ Query latency: {duration * 1000:.2f}ms")

    except Exception as e:
        logger.error(f"Database test failed: {e}", exc_info=True)
        click.echo(f"✗ Database test failed: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@debug.command()
def test_redis() -> None:
    """
    Test Redis connection.

    Example:
        python -m app.cli debug test-redis
    """
    try:
        import redis
        from app.core.config import get_settings

        settings = get_settings()

        click.echo("Testing Redis connection...")

        r = redis.from_url(settings.redis_url_with_password)

        # Test ping
        r.ping()
        click.echo("✓ Redis connection successful")

        # Get info
        info = r.info()
        click.echo(f"✓ Redis version: {info['redis_version']}")
        click.echo(f"✓ Used memory: {info['used_memory_human']}")
        click.echo(f"✓ Connected clients: {info['connected_clients']}")

        # Test set/get
        r.set("test_key", "test_value", ex=10)
        value = r.get("test_key")
        assert value == b"test_value"
        click.echo("✓ Set/get operations working")

    except Exception as e:
        logger.error(f"Redis test failed: {e}", exc_info=True)
        click.echo(f"✗ Redis test failed: {e}", err=True)
        raise click.Abort()


@debug.command()
def show_config() -> None:
    """
    Show current configuration (sanitized).

    Example:
        python -m app.cli debug show-config
    """
    from app.core.config import get_settings

    try:
        settings = get_settings()

        click.echo("Current Configuration\n" + "=" * 60)

        # Display sanitized config
        config = {
            "APP_NAME": settings.APP_NAME,
            "APP_VERSION": settings.APP_VERSION,
            "DEBUG": settings.DEBUG,
            "LOG_LEVEL": settings.LOG_LEVEL,
            "LOG_FORMAT": settings.LOG_FORMAT,
            "DATABASE_URL": _sanitize_url(settings.DATABASE_URL),
            "REDIS_URL": _sanitize_url(settings.REDIS_URL),
            "CACHE_ENABLED": settings.CACHE_ENABLED,
            "DB_POOL_SIZE": settings.DB_POOL_SIZE,
            "DB_POOL_MAX_OVERFLOW": settings.DB_POOL_MAX_OVERFLOW,
        }

        for key, value in config.items():
            click.echo(f"{key}: {value}")

        click.echo("=" * 60)

    except Exception as e:
        logger.error(f"Show config failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@debug.command()
@click.option(
    "--query",
    type=str,
    required=True,
    help="SQL query to execute",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
def sql(query: str, format: str) -> None:
    """
    Execute raw SQL query (read-only recommended).

    WARNING: Use with caution. No safety checks.

    Example:
        python -m app.cli debug sql --query "SELECT COUNT(*) FROM persons"
    """
    db = SessionLocal()

    try:
        click.echo(f"Executing: {query}\n")

        result = db.execute(text(query))

        # Fetch results
        rows = result.fetchall()

        if not rows:
            click.echo("No results")
            return

        if format == "table":
            # Get column names
            columns = result.keys()

            # Calculate column widths
            widths = [len(col) for col in columns]
            for row in rows:
                for i, val in enumerate(row):
                    widths[i] = max(widths[i], len(str(val)))

            # Print header
            header = " | ".join(col.ljust(widths[i]) for i, col in enumerate(columns))
            click.echo(header)
            click.echo("-" * len(header))

            # Print rows
            for row in rows:
                line = " | ".join(
                    str(val).ljust(widths[i]) for i, val in enumerate(row)
                )
                click.echo(line)

            click.echo(f"\n{len(rows)} rows")

        elif format == "json":
            import json

            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            click.echo(json.dumps(data, indent=2, default=str))

        elif format == "csv":
            import csv
            import sys

            writer = csv.writer(sys.stdout)
            writer.writerow(result.keys())
            writer.writerows(rows)

    except Exception as e:
        logger.error(f"SQL execution failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@debug.command()
def env_check() -> None:
    """
    Check environment variables and requirements.

    Example:
        python -m app.cli debug env-check
    """
    import os

    try:
        click.echo("Environment Check\n" + "=" * 60)

        # Required environment variables
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY",
        ]

        optional_vars = [
            "LOG_LEVEL",
            "DEBUG",
            "REDIS_PASSWORD",
        ]

        # Check required variables
        click.echo("\nRequired Variables:")
        for var in required_vars:
            value = os.getenv(var)
            if value:
                sanitized = _sanitize_value(value)
                click.echo(f"  ✓ {var}: {sanitized}")
            else:
                click.echo(f"  ✗ {var}: NOT SET", err=True)

        # Check optional variables
        click.echo("\nOptional Variables:")
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                click.echo(f"  ✓ {var}: {value}")
            else:
                click.echo(f"  - {var}: not set (using default)")

        # Check Python version
        click.echo(f"\nPython Version: {sys.version}")

        click.echo("=" * 60)

    except Exception as e:
        logger.error(f"Environment check failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


def _sanitize_url(url: str) -> str:
    """Sanitize URL by hiding password."""
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url)

    if parsed.password:
        netloc = f"{parsed.username}:***@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"

        sanitized = urlunparse(
            (
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
        return sanitized

    return url


def _sanitize_value(value: str) -> str:
    """Sanitize sensitive value."""
    if len(value) > 20:
        return value[:8] + "..." + value[-4:]
    return "***"
