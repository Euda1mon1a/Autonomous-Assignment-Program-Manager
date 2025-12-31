"""Database schema migration CLI commands (Alembic wrapper)."""

from pathlib import Path
from typing import Optional

import click

from app.core.logging import get_logger

logger = get_logger(__name__)


@click.group()
def schema() -> None:
    """Database schema migration commands (Alembic wrapper)."""
    pass


@schema.command()
@click.option(
    "--message",
    "-m",
    type=str,
    required=True,
    help="Migration message",
)
@click.option(
    "--autogenerate",
    is_flag=True,
    help="Auto-generate migration from model changes",
)
def create(message: str, autogenerate: bool) -> None:
    """
    Create a new database schema migration.

    Example:
        python -m app.cli schema create -m "Add new field" --autogenerate
        python -m app.cli schema create -m "Custom migration"
    """
    import subprocess

    try:
        click.echo(f"Creating migration: {message}")

        cmd = ["alembic", "revision"]

        if autogenerate:
            cmd.append("--autogenerate")

        cmd.extend(["-m", message])

        result = subprocess.run(
            cmd,
            cwd="backend",
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            click.echo(f"Error: {result.stderr}", err=True)
            raise click.Abort()

        click.echo(result.stdout)
        click.echo("✓ Migration created successfully")

        if autogenerate:
            click.echo("\nWARNING: Review the generated migration file before applying!")
            click.echo("Autogenerate is not perfect and may miss some changes.")

    except Exception as e:
        logger.error(f"Migration creation failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@schema.command()
@click.option(
    "--revision",
    type=str,
    default="head",
    help="Target revision (default: head)",
)
@click.option(
    "--sql",
    is_flag=True,
    help="Generate SQL without applying",
)
def upgrade(revision: str, sql: bool) -> None:
    """
    Upgrade database to a later version.

    Example:
        python -m app.cli schema upgrade
        python -m app.cli schema upgrade --revision +1
        python -m app.cli schema upgrade --sql
    """
    import subprocess

    try:
        click.echo(f"Upgrading database to: {revision}")

        cmd = ["alembic", "upgrade"]

        if sql:
            cmd.append("--sql")

        cmd.append(revision)

        result = subprocess.run(
            cmd,
            cwd="backend",
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            click.echo(f"Error: {result.stderr}", err=True)
            raise click.Abort()

        click.echo(result.stdout)

        if not sql:
            click.echo("✓ Database upgraded successfully")

    except Exception as e:
        logger.error(f"Migration upgrade failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@schema.command()
@click.option(
    "--revision",
    type=str,
    default="-1",
    help="Target revision (default: -1 = one step back)",
)
@click.option(
    "--sql",
    is_flag=True,
    help="Generate SQL without applying",
)
def downgrade(revision: str, sql: bool) -> None:
    """
    Downgrade database to a previous version.

    Example:
        python -m app.cli schema downgrade
        python -m app.cli schema downgrade --revision base
        python -m app.cli schema downgrade --sql
    """
    import subprocess

    try:
        click.echo(f"Downgrading database to: {revision}")

        if not sql:
            if not click.confirm(
                "WARNING: Downgrading may cause data loss. Continue?"
            ):
                click.echo("Aborted")
                return

        cmd = ["alembic", "downgrade"]

        if sql:
            cmd.append("--sql")

        cmd.append(revision)

        result = subprocess.run(
            cmd,
            cwd="backend",
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            click.echo(f"Error: {result.stderr}", err=True)
            raise click.Abort()

        click.echo(result.stdout)

        if not sql:
            click.echo("✓ Database downgraded successfully")

    except Exception as e:
        logger.error(f"Migration downgrade failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@schema.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed migration information",
)
def history(verbose: bool) -> None:
    """
    Show migration history.

    Example:
        python -m app.cli schema history
        python -m app.cli schema history --verbose
    """
    import subprocess

    try:
        cmd = ["alembic", "history"]

        if verbose:
            cmd.append("--verbose")

        result = subprocess.run(
            cmd,
            cwd="backend",
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            click.echo(f"Error: {result.stderr}", err=True)
            raise click.Abort()

        click.echo(result.stdout)

    except Exception as e:
        logger.error(f"Migration history failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@schema.command()
def current() -> None:
    """
    Show current migration revision.

    Example:
        python -m app.cli schema current
    """
    import subprocess

    try:
        result = subprocess.run(
            ["alembic", "current"],
            cwd="backend",
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            click.echo(f"Error: {result.stderr}", err=True)
            raise click.Abort()

        click.echo(result.stdout)

    except Exception as e:
        logger.error(f"Get current revision failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@schema.command()
@click.option(
    "--revision",
    type=str,
    required=True,
    help="Revision to show",
)
def show(revision: str) -> None:
    """
    Show details of a specific migration.

    Example:
        python -m app.cli schema show --revision head
        python -m app.cli schema show --revision abc123
    """
    import subprocess

    try:
        result = subprocess.run(
            ["alembic", "show", revision],
            cwd="backend",
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            click.echo(f"Error: {result.stderr}", err=True)
            raise click.Abort()

        click.echo(result.stdout)

    except Exception as e:
        logger.error(f"Show migration failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
