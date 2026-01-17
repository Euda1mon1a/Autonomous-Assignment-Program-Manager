"""Database schema migration CLI commands (Alembic wrapper)."""

import json
from pathlib import Path
from typing import Any, Optional

import click
from sqlalchemy import inspect

from app.core.logging import get_logger

logger = get_logger(__name__)

# Domain mappings for schema visualization
# Maps table names to logical domains for visual grouping
TABLE_DOMAINS: dict[str, str] = {
    # Core Scheduling
    "people": "Core Scheduling",
    "blocks": "Core Scheduling",
    "assignments": "Core Scheduling",
    "schedule_runs": "Core Scheduling",
    # Rotations
    "rotation_templates": "Rotations",
    "weekly_patterns": "Rotations",
    "rotation_preferences": "Rotations",
    "rotation_halfday_requirements": "Rotations",
    "rotation_activity_requirements": "Rotations",
    "resident_weekly_requirements": "Rotations",
    "block_assignments": "Rotations",
    # Activities
    "activities": "Activities",
    "activity_categories": "Activities",
    # Half-Day Scheduling (TAMC)
    "half_day_assignments": "Half-Day Scheduling",
    "inpatient_preloads": "Half-Day Scheduling",
    "resident_call_preloads": "Half-Day Scheduling",
    "intern_stagger_patterns": "Half-Day Scheduling",
    # Absences & Call
    "absences": "Absences & Call",
    "call_assignments": "Absences & Call",
    # Swaps
    "swap_records": "Swaps",
    "swap_approvals": "Swaps",
    # Drafts
    "schedule_drafts": "Drafts",
    "schedule_draft_assignments": "Drafts",
    "schedule_draft_flags": "Drafts",
    # Import/Export
    "import_batches": "Import/Export",
    "import_staged_assignments": "Import/Export",
    "export_jobs": "Import/Export",
    "export_job_executions": "Import/Export",
    "export_templates": "Import/Export",
    # Clinic Sessions
    "clinic_sessions": "Clinic Sessions",
    # Faculty Configuration
    "faculty_preferences": "Faculty Configuration",
    "faculty_weekly_templates": "Faculty Configuration",
    "faculty_weekly_overrides": "Faculty Configuration",
    # Credentialing
    "procedures": "Credentialing",
    "procedure_credentials": "Credentialing",
    "person_certifications": "Credentialing",
    # Notifications
    "notifications": "Notifications",
    "notification_preferences": "Notifications",
    "scheduled_notifications": "Notifications",
    "email_logs": "Notifications",
    "email_templates": "Notifications",
    # Webhooks
    "webhooks": "Webhooks",
    "webhook_deliveries": "Webhooks",
    "webhook_dead_letters": "Webhooks",
    # Auth & Users
    "users": "Auth & Users",
    "token_blacklist": "Auth & Users",
    "api_keys": "Auth & Users",
    "oauth2_clients": "Auth & Users",
    "ip_whitelist": "Auth & Users",
    "ip_blacklist": "Auth & Users",
    "request_signatures": "Auth & Users",
    "pkce_clients": "Auth & Users",
    "oauth2_authorization_codes": "Auth & Users",
    # Conflict Management
    "conflict_alerts": "Conflict Management",
    "approval_records": "Conflict Management",
    # Resilience Tier 1
    "resilience_health_checks": "Resilience T1",
    "resilience_events": "Resilience T1",
    "sacrifice_decisions": "Resilience T1",
    "fallback_activations": "Resilience T1",
    "vulnerability_records": "Resilience T1",
    # Resilience Tier 2
    "allostasis_records": "Resilience T2",
    "positive_feedback_alerts": "Resilience T2",
    "scheduling_zone_records": "Resilience T2",
    "zone_faculty_assignment_records": "Resilience T2",
    "zone_borrowing_records": "Resilience T2",
    "zone_incident_records": "Resilience T2",
    "equilibrium_shift_records": "Resilience T2",
    "system_stress_records": "Resilience T2",
    "compensation_records": "Resilience T2",
    # Resilience Tier 3
    "cognitive_session_records": "Resilience T3",
    "cognitive_decision_records": "Resilience T3",
    "preference_trail_records": "Resilience T3",
    "trail_signal_records": "Resilience T3",
    "faculty_centrality_records": "Resilience T3",
    "hub_protection_plan_records": "Resilience T3",
    "cross_training_recommendation_records": "Resilience T3",
    # Wellness & Surveys
    "surveys": "Wellness",
    "survey_responses": "Wellness",
    "wellness_accounts": "Wellness",
    "wellness_point_transactions": "Wellness",
    "wellness_leaderboard_snapshots": "Wellness",
    "hopfield_positions": "Wellness",
    "survey_availabilities": "Wellness",
    # Agent Memory
    "task_history": "AI Agents",
    "agent_embeddings": "AI Agents",
    "rag_documents": "AI Agents",
    # Jobs & Tasks
    "scheduled_jobs": "Jobs & Tasks",
    "job_executions": "Jobs & Tasks",
    "idempotency_requests": "Jobs & Tasks",
    # State Machines
    "state_machine_instances": "State Machines",
    "state_machine_transitions": "State Machines",
    # Activity Logs
    "activity_logs": "Audit",
    # Feature Flags
    "feature_flags": "Feature Flags",
    "feature_flag_evaluations": "Feature Flags",
    "feature_flag_audits": "Feature Flags",
    # Schema Management
    "schema_versions": "Schema Management",
    "schema_change_events": "Schema Management",
    # Calendar
    "calendar_subscriptions": "Calendar",
    # Day Types
    "day_types": "Day Types",
    # Settings
    "application_settings": "Settings",
    # Game Theory
    "faculty_egalitarian_scores": "Game Theory",
    "egalitarian_score_snapshots": "Game Theory",
}

# Domain colors for visualization
DOMAIN_COLORS: dict[str, str] = {
    "Core Scheduling": "#3b82f6",  # Blue
    "Rotations": "#8b5cf6",  # Purple
    "Activities": "#6366f1",  # Indigo
    "Half-Day Scheduling": "#0ea5e9",  # Sky blue
    "Absences & Call": "#f97316",  # Orange
    "Swaps": "#eab308",  # Yellow
    "Drafts": "#84cc16",  # Lime
    "Import/Export": "#14b8a6",  # Teal
    "Clinic Sessions": "#ec4899",  # Pink
    "Faculty Configuration": "#a855f7",  # Violet
    "Credentialing": "#06b6d4",  # Cyan
    "Notifications": "#f59e0b",  # Amber
    "Webhooks": "#78716c",  # Stone
    "Auth & Users": "#ef4444",  # Red
    "Conflict Management": "#dc2626",  # Red-600
    "Resilience T1": "#22c55e",  # Green
    "Resilience T2": "#16a34a",  # Green-600
    "Resilience T3": "#15803d",  # Green-700
    "Wellness": "#d946ef",  # Fuchsia
    "AI Agents": "#0284c7",  # Sky-600
    "Jobs & Tasks": "#64748b",  # Slate
    "State Machines": "#7c3aed",  # Violet-600
    "Audit": "#475569",  # Slate-600
    "Feature Flags": "#ca8a04",  # Yellow-600
    "Schema Management": "#737373",  # Neutral
    "Calendar": "#2563eb",  # Blue-600
    "Day Types": "#9333ea",  # Purple-600
    "Settings": "#52525b",  # Zinc-600
    "Game Theory": "#c026d3",  # Fuchsia-600
}


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
            click.echo(
                "\nWARNING: Review the generated migration file before applying!"
            )
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
            if not click.confirm("WARNING: Downgrading may cause data loss. Continue?"):
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


def _get_column_type_name(column_type: Any) -> str:
    """Get a clean string representation of a SQLAlchemy column type."""
    type_str = str(column_type)
    # Clean up common type representations
    if "UUID" in type_str or "GUID" in type_str:
        return "UUID"
    if "VARCHAR" in type_str:
        # Extract length if present
        import re

        match = re.search(r"VARCHAR\((\d+)\)", type_str)
        if match:
            return f"VARCHAR({match.group(1)})"
        return "VARCHAR"
    if "INTEGER" in type_str:
        return "INTEGER"
    if "BOOLEAN" in type_str:
        return "BOOLEAN"
    if "DATETIME" in type_str or "TIMESTAMP" in type_str:
        return "DATETIME"
    if "TEXT" in type_str:
        return "TEXT"
    if "FLOAT" in type_str:
        return "FLOAT"
    if "JSON" in type_str:
        return "JSON"
    if "ARRAY" in type_str:
        return "ARRAY"
    if "DATE" in type_str:
        return "DATE"
    if "TIME" in type_str:
        return "TIME"
    if "NUMERIC" in type_str:
        return "NUMERIC"
    if "BIGINT" in type_str:
        return "BIGINT"
    if "SMALLINT" in type_str:
        return "SMALLINT"
    return type_str


def _extract_schema_from_models() -> dict[str, Any]:
    """
    Extract schema information from SQLAlchemy models.

    Returns a dictionary with tables, foreign_keys, and domains.
    """
    # Import all models to ensure they're registered
    from app.db.base import Base

    # Import models module to trigger all model definitions
    import app.models  # noqa: F401
    import app.webhooks.models  # noqa: F401

    tables: list[dict[str, Any]] = []
    foreign_keys: list[dict[str, str]] = []
    domain_tables: dict[str, list[str]] = {}

    # Get all tables from the metadata
    for table_name, table in Base.metadata.tables.items():
        # Skip Alembic version table
        if table_name == "alembic_version":
            continue

        # Extract columns
        columns: list[dict[str, Any]] = []
        for column in table.columns:
            col_info = {
                "name": column.name,
                "type": _get_column_type_name(column.type),
                "nullable": column.nullable,
            }
            if column.primary_key:
                col_info["pk"] = True
            if column.unique:
                col_info["unique"] = True
            if column.default is not None:
                col_info["has_default"] = True
            columns.append(col_info)

        # Determine domain
        domain = TABLE_DOMAINS.get(table_name, "Other")

        # Track tables by domain
        if domain not in domain_tables:
            domain_tables[domain] = []
        domain_tables[domain].append(table_name)

        tables.append(
            {
                "name": table_name,
                "domain": domain,
                "columns": columns,
            }
        )

        # Extract foreign keys
        for fk in table.foreign_keys:
            fk_info = {
                "from": f"{table_name}.{fk.parent.name}",
                "to": f"{fk.column.table.name}.{fk.column.name}",
            }
            foreign_keys.append(fk_info)

    # Build domains list
    domains: list[dict[str, Any]] = []
    for domain_name, table_list in domain_tables.items():
        domains.append(
            {
                "name": domain_name,
                "color": DOMAIN_COLORS.get(domain_name, "#6b7280"),
                "tables": sorted(table_list),
            }
        )

    # Sort domains by name (with Core Scheduling first)
    def domain_sort_key(d: dict) -> tuple[int, str]:
        if d["name"] == "Core Scheduling":
            return (0, d["name"])
        if d["name"] == "Other":
            return (2, d["name"])
        return (1, d["name"])

    domains.sort(key=domain_sort_key)

    return {
        "tables": sorted(tables, key=lambda t: (t["domain"], t["name"])),
        "foreign_keys": foreign_keys,
        "domains": domains,
        "meta": {
            "total_tables": len(tables),
            "total_foreign_keys": len(foreign_keys),
            "total_domains": len(domains),
        },
    }


@schema.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path (default: frontend/public/data/schema.json)",
)
@click.option(
    "--pretty",
    is_flag=True,
    default=True,
    help="Pretty-print JSON output (default: True)",
)
def export(output: str | None, pretty: bool) -> None:
    """
    Export database schema to JSON for visualization.

    Extracts all tables, columns, foreign keys, and domain groupings
    from SQLAlchemy models and writes to a JSON file.

    Example:
        python -m app.cli schema export
        python -m app.cli schema export -o custom/path/schema.json
    """
    try:
        click.echo("Extracting schema from SQLAlchemy models...")

        schema_data = _extract_schema_from_models()

        # Determine output path
        if output is None:
            # Default to frontend/public/data/schema.json
            output_path = Path(__file__).parent.parent.parent.parent.parent / (
                "frontend/public/data/schema.json"
            )
        else:
            output_path = Path(output)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON file
        indent = 2 if pretty else None
        with open(output_path, "w") as f:
            json.dump(schema_data, f, indent=indent)

        click.echo(f"Schema exported to: {output_path}")
        click.echo(f"  Tables: {schema_data['meta']['total_tables']}")
        click.echo(f"  Foreign Keys: {schema_data['meta']['total_foreign_keys']}")
        click.echo(f"  Domains: {schema_data['meta']['total_domains']}")

        # Show domain summary
        click.echo("\nDomain Summary:")
        for domain in schema_data["domains"]:
            click.echo(f"  {domain['name']}: {len(domain['tables'])} tables")

    except Exception as e:
        logger.error(f"Schema export failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
