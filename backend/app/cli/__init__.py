"""
Command-line interface for Residency Scheduler.

This package provides CLI commands for:
- Schedule management and generation
- User and role management
- ACGME compliance checking
- Data import/export
- Database maintenance
- System debugging

Usage:
    python -m app.cli [COMMAND] [OPTIONS]
    python -m app.cli --help

Examples:
    python -m app.cli schedule generate --start 2025-07-01 --end 2025-09-30
    python -m app.cli user create --email admin@example.com --role ADMIN
    python -m app.cli compliance check --start 2025-07-01
    python -m app.cli data export --format json --output schedule.json
"""

__version__ = "1.0.0"
