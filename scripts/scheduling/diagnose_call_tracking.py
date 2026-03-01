#!/usr/bin/env python3
"""Diagnose CALL code tracking gaps between half_day_assignments and call_assignments.

Checks:
1. HDAs with CALL activity that have no matching call_assignments row
2. call_assignments with call_type not in the equity filter ('weekend','overnight','holiday')
3. PCAT/DO generation analysis: which calls produce next-day codes and why

Usage:
    cd backend && python -m scripts.scheduling.diagnose_call_tracking
    # OR
    cd backend && PYTHONPATH=. python ../scripts/scheduling/diagnose_call_tracking.py
"""

import os
import sys

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
sys.path.insert(0, os.path.abspath(backend_dir))

os.environ.setdefault("SKIP_SETTINGS_VALIDATION", "1")

import psycopg2

DSN = "postgresql://scheduler:scheduler@localhost:5432/residency_scheduler"


def get_conn():
    return psycopg2.connect(DSN)


def check_1_orphaned_call_hdas(conn):
    """Find HDAs with CALL activity code that have no matching call_assignments row."""
    print("\n=== Check 1: CALL HDAs without matching call_assignments ===")
    cur = conn.cursor()
    cur.execute("""
        SELECT
            p.name,
            h.date,
            h.time_of_day,
            a.code AS activity_code,
            h.source
        FROM half_day_assignments h
        JOIN activities a ON h.activity_id = a.id
        JOIN people p ON h.person_id = p.id
        LEFT JOIN call_assignments ca ON (
            ca.person_id = h.person_id
            AND ca.date = h.date
        )
        WHERE a.code IN ('CALL', 'call', 'Staff Call')
          AND ca.id IS NULL
        ORDER BY p.name, h.date
    """)
    rows = cur.fetchall()
    if rows:
        print(f"  FOUND {len(rows)} orphaned CALL HDAs (no call_assignments row):")
        for name, dt, tod, code, source in rows:
            print(f"    {name}: {dt} {tod} [{code}] source={source}")
    else:
        print("  OK — all CALL HDAs have matching call_assignments rows")
    return rows


def check_2_call_types(conn):
    """Check call_assignments for non-standard call_type values."""
    print("\n=== Check 2: call_assignments call_type distribution ===")
    cur = conn.cursor()
    cur.execute("""
        SELECT
            ca.call_type,
            ca.is_weekend,
            COUNT(*) as cnt,
            ARRAY_AGG(DISTINCT p.name) as faculty_names
        FROM call_assignments ca
        JOIN people p ON ca.person_id = p.id
        GROUP BY ca.call_type, ca.is_weekend
        ORDER BY ca.call_type, ca.is_weekend
    """)
    rows = cur.fetchall()
    equity_types = {"weekend", "overnight", "holiday"}
    print(f"  Equity query filters: {equity_types}")
    for call_type, is_weekend, cnt, names in rows:
        in_equity = call_type in equity_types
        marker = "OK" if in_equity else "EXCLUDED"
        print(f"  [{marker}] call_type='{call_type}' is_weekend={is_weekend}: {cnt} rows")
        if not in_equity:
            print(f"    Faculty: {', '.join(names[:5])}")
    return rows


def check_3_pcat_do_analysis(conn):
    """Analyze which calls produce PCAT+DO next-day codes and which don't."""
    print("\n=== Check 3: PCAT/DO generation analysis ===")
    cur = conn.cursor()

    # Get all call_assignments for Block 12
    cur.execute("""
        SELECT
            p.name,
            ca.date AS call_date,
            ca.call_type,
            ca.is_weekend,
            -- Check for PCAT next day AM
            (SELECT a.code FROM half_day_assignments h2
             JOIN activities a ON h2.activity_id = a.id
             WHERE h2.person_id = ca.person_id
               AND h2.date = ca.date + INTERVAL '1 day'
               AND h2.time_of_day = 'AM'
               AND a.code IN ('PCAT', 'pcat')
             LIMIT 1) AS next_day_am,
            -- Check for DO next day PM
            (SELECT a.code FROM half_day_assignments h2
             JOIN activities a ON h2.activity_id = a.id
             WHERE h2.person_id = ca.person_id
               AND h2.date = ca.date + INTERVAL '1 day'
               AND h2.time_of_day = 'PM'
               AND a.code IN ('DO', 'do')
             LIMIT 1) AS next_day_pm,
            -- Check if next day is FMIT
            (SELECT a.code FROM half_day_assignments h2
             JOIN activities a ON h2.activity_id = a.id
             WHERE h2.person_id = ca.person_id
               AND h2.date = ca.date + INTERVAL '1 day'
               AND h2.time_of_day = 'AM'
               AND a.code = 'FMIT'
             LIMIT 1) AS next_day_fmit,
            EXTRACT(DOW FROM ca.date) AS day_of_week
        FROM call_assignments ca
        JOIN people p ON ca.person_id = p.id
        WHERE ca.date >= '2026-05-07' AND ca.date <= '2026-06-03'
        ORDER BY ca.date, p.name
    """)
    rows = cur.fetchall()
    total = len(rows)
    with_pcat = sum(1 for r in rows if r[4] is not None)
    with_do = sum(1 for r in rows if r[5] is not None)

    print(f"  Total calls in Block 12: {total}")
    print(f"  With PCAT next-day AM: {with_pcat}")
    print(f"  With DO next-day PM: {with_do}")
    print()

    for name, call_date, call_type, is_weekend, pcat, do, fmit, dow in rows:
        pcat_str = pcat or "—"
        do_str = do or "—"
        reason = ""
        if not pcat and not do:
            if fmit:
                reason = "(FMIT next day — skip expected)"
            elif dow in (5, 6):  # Fri=5, Sat=6 in PG DOW
                reason = "(weekend call — recovery expected)"
            else:
                reason = "(UNEXPECTED: no PCAT/DO and no FMIT/weekend)"
        marker = "OK" if pcat and do else "SKIP"
        print(
            f"  [{marker}] {name}: {call_date} (dow={int(dow)}) "
            f"type={call_type} wknd={is_weekend} → PCAT={pcat_str} DO={do_str} {reason}"
        )
    return rows


def check_4_equity_query_results(conn):
    """Show who appears in the overnight equity query vs who has CALL HDAs."""
    print("\n=== Check 4: Equity query vs CALL HDA comparison ===")
    cur = conn.cursor()

    # Equity query (mirrors engine.py:983-1020)
    cur.execute("""
        SELECT
            p.name,
            CASE
                WHEN ca.call_type = 'overnight' AND ca.is_weekend = TRUE THEN 'weekend'
                ELSE ca.call_type
            END AS effective_type,
            COUNT(*) AS cnt
        FROM call_assignments ca
        JOIN people p ON ca.person_id = p.id
        WHERE ca.date >= '2025-07-01'
          AND ca.date < '2026-06-04'
          AND ca.call_type IN ('weekend', 'overnight', 'holiday')
        GROUP BY p.name, effective_type
        ORDER BY p.name, effective_type
    """)
    equity_rows = cur.fetchall()

    # CALL HDAs
    cur.execute("""
        SELECT DISTINCT p.name
        FROM half_day_assignments h
        JOIN activities a ON h.activity_id = a.id
        JOIN people p ON h.person_id = p.id
        WHERE a.code IN ('CALL', 'call', 'Staff Call')
          AND h.date >= '2026-05-07' AND h.date <= '2026-06-03'
    """)
    hda_names = {r[0] for r in cur.fetchall()}

    equity_names = {r[0] for r in equity_rows}

    print(f"  Faculty with CALL HDAs: {sorted(hda_names)}")
    print(f"  Faculty in equity query: {sorted(equity_names)}")
    print(f"  In HDAs but NOT equity: {sorted(hda_names - equity_names)}")
    print(f"  In equity but NOT HDAs: {sorted(equity_names - hda_names)}")
    print()

    if equity_rows:
        print("  Equity breakdown:")
        for name, etype, cnt in equity_rows:
            print(f"    {name}: {etype}={cnt}")

    return equity_rows


if __name__ == "__main__":
    print("=" * 60)
    print("CALL Code Tracking Diagnostic")
    print("=" * 60)

    conn = get_conn()
    try:
        orphaned = check_1_orphaned_call_hdas(conn)
        types = check_2_call_types(conn)
        pcat_do = check_3_pcat_do_analysis(conn)
        equity = check_4_equity_query_results(conn)

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"  Orphaned CALL HDAs: {len(orphaned)}")
        print(f"  Call types in DB: {len(types)}")
        print(f"  Calls in Block 12: {len(pcat_do)}")
        print(f"  Calls with PCAT/DO: {sum(1 for r in pcat_do if r[4])}/{len(pcat_do)}")
    finally:
        conn.close()
