"""Export API routes for CSV, JSON, and Excel data export."""

import csv
import io
import json
import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.dependencies.role_filter import require_admin
from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.user import User
from app.services.xlsx_export import generate_legacy_xlsx

router = APIRouter()
logger = logging.getLogger(__name__)


def generate_csv(headers: list[str], rows: list[list]) -> str:
    """Generate CSV content from headers and rows."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue()


def create_csv_response(content: str, filename: str) -> StreamingResponse:
    """Create a streaming response for CSV download."""
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def create_json_response(data: list, filename: str) -> StreamingResponse:
    """Create a streaming response for JSON download."""
    content = json.dumps(data, indent=2, default=str)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/people")
async def export_people(
    format: str = Query("csv", description="Export format: csv or json"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Export all people data. Requires admin role.

    Returns CSV or JSON with columns: Name, Type, PGY Level, Email
    """
    people = db.query(Person).order_by(Person.name).all()

    if format == "json":
        data = [
            {
                "name": p.name,
                "type": p.type,
                "pgy_level": p.pgy_level,
                "email": p.email,
                "specialties": p.specialties,
                "performs_procedures": p.performs_procedures,
            }
            for p in people
        ]
        return create_json_response(data, "people.json")

    # Default to CSV
    headers = ["Name", "Type", "PGY Level", "Email"]
    rows = [[p.name, p.type, p.pgy_level or "", p.email or ""] for p in people]
    content = generate_csv(headers, rows)
    return create_csv_response(content, "people.csv")


@router.get("/absences")
async def export_absences(
    format: str = Query("csv", description="Export format: csv or json"),
    start_date: date | None = Query(None, description="Filter absences starting from"),
    end_date: date | None = Query(None, description="Filter absences ending by"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Export absences data. Requires admin role.

    Returns CSV or JSON with columns: Person, Type, Start Date, End Date, Notes
    """
    query = db.query(Absence).options(joinedload(Absence.person))

    if start_date:
        query = query.filter(Absence.end_date >= start_date)
    if end_date:
        query = query.filter(Absence.start_date <= end_date)

    absences = query.order_by(Absence.start_date).all()

    if format == "json":
        data = [
            {
                "person_name": a.person.name if a.person else "Unknown",
                "absence_type": a.absence_type,
                "start_date": a.start_date.isoformat() if a.start_date else None,
                "end_date": a.end_date.isoformat() if a.end_date else None,
                "notes": a.notes,
                "deployment_orders": a.deployment_orders,
                "tdy_location": a.tdy_location,
            }
            for a in absences
        ]
        return create_json_response(data, "absences.json")

    # Default to CSV
    headers = ["Person", "Type", "Start Date", "End Date", "Notes"]
    rows = [
        [
            a.person.name if a.person else "Unknown",
            a.absence_type,
            a.start_date.isoformat() if a.start_date else "",
            a.end_date.isoformat() if a.end_date else "",
            a.notes or "",
        ]
        for a in absences
    ]
    content = generate_csv(headers, rows)
    return create_csv_response(content, "absences.csv")


@router.get("/schedule")
async def export_schedule(
    format: str = Query("csv", description="Export format: csv or json"),
    start_date: date = Query(..., description="Schedule start date"),
    end_date: date = Query(..., description="Schedule end date"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Export schedule data for a date range. Requires admin role.

    Returns CSV or JSON with columns: Date, Time, Person, Role, Activity
    """
    assignments = (
        db.query(Assignment)
        .options(
            joinedload(Assignment.block),
            joinedload(Assignment.person),
            joinedload(Assignment.rotation_template),
        )
        .join(Block)
        .filter(Block.date >= start_date, Block.date <= end_date)
        .order_by(Block.date, Block.time_of_day)
        .all()
    )

    if format == "json":
        data = [
            {
                "date": a.block.date.isoformat() if a.block else None,
                "time_of_day": a.block.time_of_day if a.block else None,
                "person_name": a.person.name if a.person else "Unknown",
                "person_type": a.person.type if a.person else None,
                "pgy_level": a.person.pgy_level if a.person else None,
                "role": a.role,
                "activity": a.activity_name,
                "notes": a.notes,
            }
            for a in assignments
        ]
        return create_json_response(data, "schedule.json")

    # Default to CSV
    headers = ["Date", "Time", "Person", "Type", "PGY Level", "Role", "Activity"]
    rows = [
        [
            a.block.date.isoformat() if a.block else "",
            a.block.time_of_day if a.block else "",
            a.person.name if a.person else "Unknown",
            a.person.type if a.person else "",
            a.person.pgy_level if a.person else "",
            a.role,
            a.activity_name or "",
        ]
        for a in assignments
    ]
    content = generate_csv(headers, rows)
    return create_csv_response(content, "schedule.csv")


@router.get("/schedule/xlsx")
async def export_schedule_xlsx(
    start_date: date = Query(..., description="Schedule start date"),
    end_date: date = Query(..., description="Schedule end date"),
    block_number: int | None = Query(
        None, description="Block number for header (auto-calculated if not provided)"
    ),
    federal_holidays: str | None = Query(
        None, description="Comma-separated federal holiday dates (YYYY-MM-DD)"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Export schedule in legacy Excel format. Requires admin role.

    This generates an Excel file matching the historical format used for
    schedule distribution with:
    - AM/PM columns per day
    - Color-coded rotation labels
    - PGY level grouping
    - Federal holiday highlighting

    Args:
        start_date: Start date of the block (typically 28 days)
        end_date: End date of the block
        block_number: Block number to display in header (1-13 for academic year)
        federal_holidays: Comma-separated list of holiday dates to highlight

    Returns:
        Excel file (.xlsx) download
    """
    # Parse federal holidays if provided
    holidays: list[date] = []
    if federal_holidays:
        try:
            for date_str in federal_holidays.split(","):
                date_str = date_str.strip()
                if date_str:
                    holidays.append(datetime.strptime(date_str, "%Y-%m-%d").date())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format in federal_holidays. Use YYYY-MM-DD format",
            )

    try:
        xlsx_bytes = generate_legacy_xlsx(
            db=db,
            start_date=start_date,
            end_date=end_date,
            block_number=block_number,
            federal_holidays=holidays,
        )
    except Exception:
        raise HTTPException(
            status_code=500, detail="An error occurred generating the Excel file"
        )

    # Generate filename with date range
    filename = (
        f"schedule_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
    )

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
