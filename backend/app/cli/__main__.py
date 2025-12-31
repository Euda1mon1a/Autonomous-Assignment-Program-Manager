#!/usr/bin/env python3
"""
Main CLI entry point for Residency Scheduler.

This is the primary command-line interface for managing the scheduling system.
Provides commands for schedule generation, user management, compliance checking,
data operations, and system maintenance.

Usage:
    python -m app.cli [COMMAND] [OPTIONS]
    python -m app.cli --help

Examples:
    # Schedule management
    python -m app.cli schedule generate --start 2025-07-01 --end 2025-09-30
    python -m app.cli schedule validate --block 10
    python -m app.cli schedule export --format pdf --output schedule.pdf

    # User management
    python -m app.cli user create --email admin@example.com --role ADMIN
    python -m app.cli user list --role RESIDENT
    python -m app.cli user reset-password --email user@example.com

    # Compliance checking
    python -m app.cli compliance check --start 2025-07-01
    python -m app.cli compliance report --format pdf

    # Data operations
    python -m app.cli data export --format json
    python -m app.cli data import --file schedule.xlsx
    python -m app.cli data seed --type all

    # Maintenance
    python -m app.cli maintenance cleanup --days 90
    python -m app.cli maintenance vacuum
    python -m app.cli maintenance backup

    # Debugging
    python -m app.cli debug check-health
    python -m app.cli debug test-db
    python -m app.cli debug show-config
"""

import sys

import click

from app.cli.compliance_commands import compliance
from app.cli.data_commands import data
from app.cli.debug_commands import debug
from app.cli.maintenance_commands import maintenance
from app.cli.schedule_commands import schedule
from app.cli.schema_commands import schema
from app.cli.user_commands import user
from app.core.logging import get_logger

logger = get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="Residency Scheduler CLI")
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Enable debug logging",
)
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """
    Residency Scheduler - Command Line Interface.

    Comprehensive CLI for managing medical residency program scheduling,
    ACGME compliance monitoring, and system operations.
    """
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug

    if debug:
        import logging

        logging.basicConfig(level=logging.DEBUG)
        logger.debug("Debug mode enabled")


# Register command groups
cli.add_command(schedule)
cli.add_command(user)
cli.add_command(compliance)
cli.add_command(data)
cli.add_command(maintenance)
cli.add_command(schema)
cli.add_command(debug)


def main() -> int:
    """Main entry point."""
    try:
        cli(obj={})
        return 0
    except KeyboardInterrupt:
        click.echo("\nAborted by user", err=True)
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
