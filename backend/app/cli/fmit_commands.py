"""CLI commands for FMIT scheduling management."""
import typer
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

app = typer.Typer(help="FMIT scheduling management commands")


@app.command()
def scan_conflicts(
    faculty_id: Optional[str] = typer.Option(None, "--faculty", "-f", help="Filter by faculty ID"),
    days: int = typer.Option(90, "--days", "-d", help="Days ahead to scan"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json"),
):
    """
    Scan for schedule conflicts between leave and FMIT assignments.

    Checks for:
    - Leave/FMIT overlaps
    - Back-to-back FMIT weeks
    - External commitment conflicts
    """
    from app.db.session import SessionLocal
    from app.services.conflict_auto_detector import ConflictAutoDetector

    db = SessionLocal()
    try:
        detector = ConflictAutoDetector(db)

        faculty_uuid = UUID(faculty_id) if faculty_id else None
        end_date = date.today() + timedelta(days=days)

        conflicts = detector.detect_all_conflicts(
            faculty_id=faculty_uuid,
            start_date=date.today(),
            end_date=end_date,
        )

        if not conflicts:
            typer.echo(typer.style("No conflicts found!", fg=typer.colors.GREEN))
            return

        typer.echo(f"Found {len(conflicts)} conflict(s):\n")

        for c in conflicts:
            severity_color = {
                "critical": typer.colors.RED,
                "warning": typer.colors.YELLOW,
                "info": typer.colors.BLUE,
            }.get(c.severity, typer.colors.WHITE)

            typer.echo(
                f"  [{typer.style(c.severity.upper(), fg=severity_color)}] "
                f"{c.faculty_name} - {c.fmit_week}"
            )
            typer.echo(f"    Type: {c.conflict_type}")
            typer.echo(f"    {c.description}\n")

    finally:
        db.close()


@app.command()
def list_swaps(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    faculty_id: Optional[str] = typer.Option(None, "--faculty", "-f", help="Filter by faculty ID"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum records to show"),
):
    """
    List swap records with optional filters.

    Status options: pending, approved, executed, rejected, cancelled, rolled_back
    """
    from app.db.session import SessionLocal
    from app.models.swap import SwapRecord, SwapStatus

    db = SessionLocal()
    try:
        query = db.query(SwapRecord)

        if status:
            try:
                swap_status = SwapStatus(status.lower())
                query = query.filter(SwapRecord.status == swap_status)
            except ValueError:
                typer.echo(f"Invalid status: {status}", err=True)
                raise typer.Exit(1)

        if faculty_id:
            from sqlalchemy import or_
            fid = UUID(faculty_id)
            query = query.filter(
                or_(
                    SwapRecord.source_faculty_id == fid,
                    SwapRecord.target_faculty_id == fid,
                )
            )

        swaps = query.order_by(SwapRecord.requested_at.desc()).limit(limit).all()

        if not swaps:
            typer.echo("No swap records found.")
            return

        typer.echo(f"Found {len(swaps)} swap(s):\n")

        for swap in swaps:
            status_color = {
                SwapStatus.PENDING: typer.colors.YELLOW,
                SwapStatus.EXECUTED: typer.colors.GREEN,
                SwapStatus.REJECTED: typer.colors.RED,
                SwapStatus.ROLLED_BACK: typer.colors.MAGENTA,
            }.get(swap.status, typer.colors.WHITE)

            typer.echo(
                f"  [{typer.style(swap.status.value.upper(), fg=status_color)}] "
                f"ID: {swap.id}"
            )
            typer.echo(f"    Week: {swap.source_week} | Type: {swap.swap_type.value}")
            typer.echo(f"    Requested: {swap.requested_at.strftime('%Y-%m-%d %H:%M')}\n")

    finally:
        db.close()


@app.command()
def list_alerts(
    faculty_id: Optional[str] = typer.Option(None, "--faculty", "-f", help="Filter by faculty ID"),
    severity: Optional[str] = typer.Option(None, "--severity", "-s", help="Filter by severity"),
    include_resolved: bool = typer.Option(False, "--include-resolved", "-r", help="Include resolved alerts"),
):
    """
    List conflict alerts.

    Severity options: critical, warning, info
    """
    from app.db.session import SessionLocal
    from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus, ConflictSeverity

    db = SessionLocal()
    try:
        query = db.query(ConflictAlert)

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == UUID(faculty_id))

        if severity:
            try:
                sev = ConflictSeverity(severity.lower())
                query = query.filter(ConflictAlert.severity == sev)
            except ValueError:
                typer.echo(f"Invalid severity: {severity}", err=True)
                raise typer.Exit(1)

        if not include_resolved:
            query = query.filter(
                ConflictAlert.status.in_([
                    ConflictAlertStatus.NEW,
                    ConflictAlertStatus.ACKNOWLEDGED
                ])
            )

        alerts = query.order_by(ConflictAlert.fmit_week).all()

        if not alerts:
            typer.echo(typer.style("No alerts found!", fg=typer.colors.GREEN))
            return

        typer.echo(f"Found {len(alerts)} alert(s):\n")

        for alert in alerts:
            severity_color = {
                ConflictSeverity.CRITICAL: typer.colors.RED,
                ConflictSeverity.WARNING: typer.colors.YELLOW,
                ConflictSeverity.INFO: typer.colors.BLUE,
            }.get(alert.severity, typer.colors.WHITE)

            typer.echo(
                f"  [{typer.style(alert.severity.value.upper(), fg=severity_color)}] "
                f"Week: {alert.fmit_week}"
            )
            typer.echo(f"    Type: {alert.conflict_type.value}")
            typer.echo(f"    Status: {alert.status.value}")
            typer.echo(f"    {alert.description}\n")

    finally:
        db.close()


@app.command()
def stats():
    """
    Show FMIT scheduling statistics.

    Displays counts of swaps, alerts, and preferences.
    """
    from app.db.session import SessionLocal
    from app.models.swap import SwapRecord, SwapStatus
    from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus, ConflictSeverity
    from app.models.faculty_preference import FacultyPreference

    db = SessionLocal()
    try:
        # Swap stats
        total_swaps = db.query(SwapRecord).count()
        pending_swaps = db.query(SwapRecord).filter(
            SwapRecord.status == SwapStatus.PENDING
        ).count()
        executed_swaps = db.query(SwapRecord).filter(
            SwapRecord.status == SwapStatus.EXECUTED
        ).count()

        # Alert stats
        total_alerts = db.query(ConflictAlert).count()
        unresolved_alerts = db.query(ConflictAlert).filter(
            ConflictAlert.status.in_([
                ConflictAlertStatus.NEW,
                ConflictAlertStatus.ACKNOWLEDGED
            ])
        ).count()
        critical_alerts = db.query(ConflictAlert).filter(
            ConflictAlert.severity == ConflictSeverity.CRITICAL,
            ConflictAlert.status.in_([
                ConflictAlertStatus.NEW,
                ConflictAlertStatus.ACKNOWLEDGED
            ])
        ).count()

        # Preference stats
        total_preferences = db.query(FacultyPreference).count()

        typer.echo("\n" + "=" * 40)
        typer.echo(typer.style("  FMIT Scheduling Statistics", bold=True))
        typer.echo("=" * 40 + "\n")

        typer.echo(typer.style("Swaps:", bold=True))
        typer.echo(f"  Total: {total_swaps}")
        typer.echo(f"  Pending: {pending_swaps}")
        typer.echo(f"  Executed: {executed_swaps}\n")

        typer.echo(typer.style("Alerts:", bold=True))
        typer.echo(f"  Total: {total_alerts}")
        typer.echo(f"  Unresolved: {unresolved_alerts}")
        if critical_alerts > 0:
            typer.echo(
                f"  Critical: {typer.style(str(critical_alerts), fg=typer.colors.RED)}"
            )
        else:
            typer.echo(f"  Critical: {critical_alerts}\n")

        typer.echo(typer.style("Preferences:", bold=True))
        typer.echo(f"  Faculty with preferences: {total_preferences}\n")

    finally:
        db.close()


@app.command()
def create_alert(
    faculty_id: str = typer.Argument(..., help="Faculty ID"),
    week: str = typer.Argument(..., help="FMIT week date (YYYY-MM-DD)"),
    conflict_type: str = typer.Option("leave_fmit_overlap", "--type", "-t", help="Conflict type"),
    severity: str = typer.Option("warning", "--severity", "-s", help="Severity level"),
    description: str = typer.Option("Manual alert", "--desc", "-d", help="Description"),
):
    """
    Manually create a conflict alert.

    Useful for testing or manually flagging issues.
    """
    from app.db.session import SessionLocal
    from app.models.conflict_alert import ConflictAlert, ConflictType, ConflictSeverity
    from uuid import uuid4

    db = SessionLocal()
    try:
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=UUID(faculty_id),
            conflict_type=ConflictType(conflict_type),
            severity=ConflictSeverity(severity),
            fmit_week=datetime.strptime(week, "%Y-%m-%d").date(),
            description=description,
        )
        db.add(alert)
        db.commit()

        typer.echo(typer.style(f"Alert created: {alert.id}", fg=typer.colors.GREEN))

    except Exception as e:
        typer.echo(f"Error creating alert: {e}", err=True)
        raise typer.Exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    app()
