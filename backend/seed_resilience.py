"""Seed resilience tables with representative data.

Uses raw SQL for tables where the ORM model columns differ
from the actual database columns (schema drift).
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.person import Person
from app.models.user import User


async def seed_resilience():
    settings = get_settings()
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    )
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        result = await db.execute(select(Person))
        people = result.scalars().all()
        if not people:
            print("No people found — seed people first.")
            return

        result = await db.execute(select(User))
        users = result.scalars().all()
        user_id = users[0].id if users else None

        # Helper
        async def count_rows(table: str) -> int:
            r = await db.execute(text(f"SELECT count(*) FROM {table}"))
            return r.scalar()

        # --- Scheduling Zones ---
        print("Seeding Scheduling Zones...")
        if await count_rows("scheduling_zones") == 0:
            zones_data = [
                ("Medicine", "inpatient", "Internal medicine rotations"),
                ("Surgery", "inpatient", "Surgical rotations"),
                ("Emergency", "inpatient", "ED rotations"),
                ("Ambulatory", "outpatient", "Clinic-based rotations"),
            ]
            for zname, ztype, desc in zones_data:
                zid = str(uuid.uuid4())
                await db.execute(
                    text(
                        """
                    INSERT INTO scheduling_zones (id, name, zone_type, description, status,
                        minimum_coverage, optimal_coverage, maximum_coverage,
                        containment_level, borrowing_limit, lending_limit, priority,
                        is_active, created_at)
                    VALUES (:id, :name, :ztype, :desc, 'green',
                        2, 4, 8, 'none', 2, 1, 5, true, :ts)
                """
                    ),
                    {
                        "id": zid,
                        "name": zname,
                        "ztype": ztype,
                        "desc": desc,
                        "ts": two_weeks_ago,
                    },
                )
                print(f"  - Zone: {zname}")
        else:
            print("  - Zones already exist")
        await db.flush()

        # Get zone IDs
        r = await db.execute(text("SELECT id, name FROM scheduling_zones"))
        zone_rows = r.fetchall()
        zones = {row[1]: row[0] for row in zone_rows}

        # --- Zone Faculty Assignments ---
        print("\nSeeding Zone Faculty Assignments...")
        if await count_rows("zone_faculty_assignments") == 0:
            zone_names = list(zones.keys())
            for i, person in enumerate(people[:12]):
                zname = zone_names[i % len(zone_names)]
                zid = zones[zname]
                role = "primary" if i < 4 else "secondary"
                await db.execute(
                    text(
                        """
                    INSERT INTO zone_faculty_assignments
                        (id, zone_id, faculty_id, faculty_name, role, assigned_at, is_available)
                    VALUES (:id, :zid, :fid, :fname, :role, :ts, true)
                """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "zid": str(zid),
                        "fid": str(person.id),
                        "fname": person.name,
                        "role": role,
                        "ts": two_weeks_ago,
                    },
                )
                print(f"  - {person.name} -> {zname} ({role})")
        else:
            print("  - Faculty assignments already exist")
        await db.flush()

        # --- Resilience Events (uses 'metadata' column, not 'event_metadata') ---
        print("\nSeeding Resilience Events...")
        if await count_rows("resilience_events") == 0:
            events_data = [
                ("health_check", "low", "Routine check completed"),
                ("defense_level_changed", "medium", "Defense level elevated"),
                ("threshold_exceeded", "high", "Coverage threshold exceeded"),
            ]
            for etype, sev, reason in events_data:
                await db.execute(
                    text(
                        """
                    INSERT INTO resilience_events
                        (id, timestamp, event_type, severity, reason, triggered_by)
                    VALUES (:id, :ts, :etype, :sev, :reason, :trig)
                """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "ts": week_ago,
                        "etype": etype,
                        "sev": sev,
                        "reason": reason,
                        "trig": f"user:{people[0].id}",
                    },
                )
                print(f"  - Event: {etype} ({sev})")
        else:
            print("  - Events already exist")
        await db.flush()

        # --- Feedback Loop States (uses loop_name, not metric_name) ---
        print("\nSeeding Feedback Loop States...")
        if await count_rows("feedback_loop_states") == 0:
            loops = [
                ("coverage_balance", "coverage_ratio", 0.85, 0.80, 0.05),
                ("workload_equity", "equity_score", 0.72, 0.70, 0.02),
                ("fatigue_management", "fatigue_index", 0.91, 0.75, 0.16),
            ]
            for loop_name, setpoint_name, current, target, dev in loops:
                await db.execute(
                    text(
                        """
                    INSERT INTO feedback_loop_states
                        (id, loop_name, setpoint_name, timestamp, target_value,
                         tolerance, is_critical, current_value, deviation,
                         deviation_severity, consecutive_deviations, trend_direction,
                         is_improving, correction_triggered, correction_type, correction_effective)
                    VALUES (:id, :ln, :sn, :ts, :tv, 0.10, :crit, :cv, :dev,
                            :dsev, 0, 'stable', :impr, :corr, :ctype, true)
                """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "ln": loop_name,
                        "sn": setpoint_name,
                        "ts": week_ago,
                        "tv": target,
                        "crit": dev > 0.10,
                        "cv": current,
                        "dev": dev,
                        "dsev": "major" if dev > 0.10 else "minor",
                        "impr": dev < 0.10,
                        "corr": dev > 0.10,
                        "ctype": "rebalance" if dev > 0.10 else None,
                    },
                )
                print(f"  - Loop: {loop_name} (dev={dev})")
        else:
            print("  - Feedback loops already exist")
        await db.flush()

        # --- Allostasis Records ---
        print("\nSeeding Allostasis Records...")
        if await count_rows("allostasis_records") == 0:
            for person in people[:8]:
                load = round(random.uniform(0.2, 0.8), 2)
                state = (
                    "homeostasis"
                    if load < 0.3
                    else (
                        "allostasis"
                        if load < 0.5
                        else "allostatic_load"
                        if load < 0.7
                        else "allostatic_overload"
                    )
                )
                await db.execute(
                    text(
                        """
                    INSERT INTO allostasis_records
                        (id, entity_id, entity_type, calculated_at,
                         consecutive_weekend_calls, nights_past_month,
                         schedule_changes_absorbed, holidays_worked_this_year,
                         overtime_hours_month, acute_stress_score,
                         chronic_stress_score, total_allostatic_load,
                         allostasis_state, risk_level)
                    VALUES (:id, :eid, 'faculty', :ts,
                            :wknd, :nights, :changes, :holidays,
                            :ot, :acute, :chronic, :load,
                            :state, :risk)
                """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "eid": str(person.id),
                        "ts": week_ago,
                        "wknd": random.randint(0, 3),
                        "nights": random.randint(2, 8),
                        "changes": random.randint(0, 4),
                        "holidays": random.randint(0, 3),
                        "ot": round(random.uniform(0, 20), 1),
                        "acute": round(random.uniform(1, 5), 1),
                        "chronic": round(random.uniform(1, 6), 1),
                        "load": load,
                        "state": state,
                        "risk": (
                            "low"
                            if load < 0.4
                            else "moderate"
                            if load < 0.6
                            else "high"
                        ),
                    },
                )
                print(f"  - {person.name}: load={load}, {state}")
        else:
            print("  - Allostasis records already exist")
        await db.flush()

        # --- Equilibrium Shifts ---
        print("\nSeeding Equilibrium Shifts...")
        if await count_rows("equilibrium_shifts") == 0:
            for stress_t, state, sustainable in [
                ("staff_reduction", "compensating", True),
                ("demand_increase", "stressed", False),
            ]:
                cap_impact = -2.0 if stress_t == "staff_reduction" else 0.0
                dem_impact = 0.0 if stress_t == "staff_reduction" else 3.0
                await db.execute(
                    text(
                        """
                    INSERT INTO equilibrium_shifts
                        (id, calculated_at, original_capacity, original_demand,
                         original_coverage_rate, stress_types,
                         total_capacity_impact, total_demand_impact,
                         compensation_types, total_compensation,
                         compensation_efficiency, new_capacity, new_demand,
                         new_coverage_rate, sustainable_capacity,
                         compensation_debt, daily_debt_rate,
                         burnout_risk, days_until_exhaustion,
                         equilibrium_state, is_sustainable)
                    VALUES (:id, :ts, 10.0, 8.0, 0.80,
                            :stypes, :ci, :di,
                            :ctypes, 1.5, 0.75,
                            :nc, :nd, :ncr, 7.5,
                            0.15, 0.01,
                            :br, :due, :state, :sust)
                """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "ts": week_ago,
                        "stypes": [stress_t],
                        "ci": cap_impact,
                        "di": dem_impact,
                        "ctypes": ["redistribution"],
                        "nc": 8.0 if stress_t == "staff_reduction" else 10.0,
                        "nd": 8.0 if stress_t == "staff_reduction" else 11.0,
                        "ncr": 0.75 if stress_t == "staff_reduction" else 0.73,
                        "br": 0.3 if sustainable else 0.5,
                        "due": 30 if sustainable else 14,
                        "state": state,
                        "sust": sustainable,
                    },
                )
                print(f"  - Shift: {stress_t} -> {state}")
        else:
            print("  - Equilibrium shifts already exist")
        await db.flush()

        # --- Cognitive Sessions ---
        print("\nSeeding Cognitive Sessions...")
        if await count_rows("cognitive_sessions") == 0:
            sess_id = str(uuid.uuid4())
            await db.execute(
                text(
                    """
                INSERT INTO cognitive_sessions
                    (id, user_id, started_at, ended_at,
                     max_decisions_before_break, total_cognitive_cost,
                     decisions_count, breaks_taken, final_state, created_at)
                VALUES (:id, :uid, :start, :end, 7, 6.5, 5, 1, 'engaged', :ts)
            """
                ),
                {
                    "id": sess_id,
                    "uid": str(user_id) if user_id else str(people[0].id),
                    "start": week_ago,
                    "end": week_ago + timedelta(hours=2),
                    "ts": week_ago,
                },
            )
            print("  - Session: 5 decisions, 1 break")

            # --- Cognitive Decisions ---
            print("\nSeeding Cognitive Decisions...")
            for cat, comp, desc, cost in [
                ("assignment", "simple", "Assign resident to wards", 1.0),
                ("swap", "moderate", "Evaluate swap request", 2.5),
                ("coverage", "complex", "Resolve coverage gap", 4.0),
            ]:
                await db.execute(
                    text(
                        """
                    INSERT INTO cognitive_decisions
                        (id, session_id, category, complexity, description,
                         outcome, estimated_cognitive_cost, actual_time_seconds,
                         created_at)
                    VALUES (:id, :sid, :cat, :comp, :desc,
                            'decided', :cost, :time, :ts)
                """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "sid": sess_id,
                        "cat": cat,
                        "comp": comp,
                        "desc": desc,
                        "cost": cost,
                        "time": cost * 60,
                        "ts": week_ago,
                    },
                )
                print(f"  - Decision: {cat} ({comp})")
        else:
            print("  - Cognitive sessions already exist")
        await db.flush()

        # --- Zone Incidents ---
        print("\nSeeding Zone Incidents...")
        if await count_rows("zone_incidents") == 0 and zones:
            first_zone_id = list(zones.values())[0]
            await db.execute(
                text(
                    """
                INSERT INTO zone_incidents
                    (id, zone_id, incident_type, severity, description,
                     started_at, resolved_at, resolution_notes, containment_successful)
                VALUES (:id, :zid, 'faculty_loss', 'moderate',
                        'Unexpected absence created coverage gap',
                        :start, :end, 'Covered by cross-zone borrowing', true)
            """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "zid": str(first_zone_id),
                    "start": week_ago,
                    "end": week_ago + timedelta(hours=4),
                },
            )
            print("  - Incident: faculty_loss")
        else:
            print("  - Zone incidents already exist")
        await db.flush()

        # --- System Stress Records ---
        print("\nSeeding System Stress Records...")
        if await count_rows("system_stress_records") == 0:
            await db.execute(
                text(
                    """
                INSERT INTO system_stress_records
                    (id, stress_type, description, applied_at, magnitude,
                     duration_days, is_acute, is_reversible,
                     capacity_impact, demand_impact,
                     is_active, resolved_at, resolution_notes)
                VALUES (:id, 'faculty_loss',
                        'Two faculty on unexpected leave',
                        :applied, 0.6, 7, true, true,
                        -0.2, 0.0, false, :resolved,
                        'Temporary coverage arranged')
            """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "applied": two_weeks_ago,
                    "resolved": week_ago,
                },
            )
            print("  - Stress: faculty_loss")
        else:
            print("  - Stress records already exist")
        await db.flush()

        await db.commit()
        print("\nResilience seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_resilience())
