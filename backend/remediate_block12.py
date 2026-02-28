import os
import sys

os.environ["DEBUG"] = "true"

from app.db.session import SessionLocal
from sqlalchemy import text
from app.models.rotation_template import RotationTemplate
from app.models.activity import Activity
from app.models.rotation_activity_requirement import RotationActivityRequirement
from app.services.sync_preload_service import SyncPreloadService
from app.scheduling.engine import SchedulingEngine
from app.services.canonical_schedule_export_service import (
    CanonicalScheduleExportService,
)

db = SessionLocal()

try:
    print("Starting remediation...")

    # B1: Fix NBN Constraint
    db.execute(
        text("""
        UPDATE rotation_activity_requirements
        SET min_halfdays = 20, target_halfdays = 24
        WHERE rotation_template_id = (SELECT id FROM rotation_templates WHERE abbreviation = 'NBN')
        AND min_halfdays > max_halfdays;
    """)
    )

    # B2: FMIT-PGY3 Requirements via ORM to handle defaults like applicable_weeks_hash
    fmit_exists = db.execute(
        text("""
        SELECT count(*) FROM rotation_activity_requirements
        WHERE rotation_template_id = (SELECT id FROM rotation_templates WHERE abbreviation = 'FMIT-PGY3')
    """)
    ).scalar()

    if not fmit_exists:
        rt = db.query(RotationTemplate).filter_by(abbreviation="FMIT-PGY3").first()
        act = db.query(Activity).filter_by(code="FMIT").first()
        if rt and act:
            req = RotationActivityRequirement(
                rotation_template_id=rt.id,
                activity_id=act.id,
                min_halfdays=0,
                max_halfdays=40,
                target_halfdays=36,
                priority=80,
                prefer_full_days=True,
            )
            db.add(req)

    # B3: Faculty Templates via SQL
    targets = ["Joseph Napierala", "Derrick Thiel", "Blake Van Brunt", "Kyle Samblanet"]
    for t in targets:
        count = db.execute(
            text(
                "SELECT count(*) FROM faculty_weekly_templates fwt JOIN people p ON fwt.person_id = p.id WHERE p.name = :name"
            ),
            {"name": t},
        ).scalar()
        if count == 0:
            db.execute(
                text("""
                INSERT INTO faculty_weekly_templates (id, person_id, day_of_week, time_of_day, week_number, activity_id, is_locked, priority)
                SELECT gen_random_uuid(), p_target.id, fwt.day_of_week, fwt.time_of_day, fwt.week_number, fwt.activity_id, fwt.is_locked, fwt.priority
                FROM faculty_weekly_templates fwt
                JOIN people p_source ON fwt.person_id = p_source.id
                CROSS JOIN people p_target
                WHERE p_source.name = 'Zach McRae' AND p_target.name = :name
            """),
                {"name": t},
            )

    db.commit()
    print("Database corrections (B1-B3) applied successfully.")

    # D1: Purge Block 12 HDAs
    db.execute(
        text(
            "DELETE FROM half_day_assignments WHERE date >= '2026-05-07' AND date <= '2026-06-03';"
        )
    )
    db.commit()
    print("Block 12 HDAs purged.")

    # D2: Run Preloader
    print("Running Preloader...")
    svc = SyncPreloadService(db)
    svc.load_all_preloads(block_number=12, academic_year=2025)
    db.commit()
    print("Preloader finished.")

    # D3: Run Solver
    from datetime import date

    print("Running CP-SAT Solver...")
    engine = SchedulingEngine(
        db, start_date=date(2026, 5, 7), end_date=date(2026, 6, 3)
    )
    engine.generate(block_number=12, academic_year=2025, algorithm="cp_sat")
    db.commit()
    print("Solver finished.")

    # D4: Export
    print("Exporting Annual Workbook...")
    export_svc = CanonicalScheduleExportService(db)
    export_svc.export_year_xlsx(
        academic_year=2025, output_path="/tmp/AY2025_Master_Schedule.xlsx"
    )
    print("Export complete: /tmp/AY2025_Master_Schedule.xlsx")

except Exception as e:
    db.rollback()
    print(f"Error occurred: {e}")
finally:
    db.close()
