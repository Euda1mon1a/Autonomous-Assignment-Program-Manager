"""Flag Memorial Day 2026 in the blocks table.

Memorial Day (May 25, 2026) is not currently flagged as a holiday in the blocks
table. This affects leave calculations, off-day handling, and template application
during the handjam import.

Usage:
  backend/.venv/bin/python scripts/data/block12_import/fix_memorial_day.py

Reference: backend/app/utils/holidays.py — is_federal_holiday()
"""

import sys
from datetime import date

import psycopg2

sys.path.insert(0, "backend")
from app.utils.holidays import is_federal_holiday

CONN = "dbname=residency_scheduler user=scheduler host=localhost"

MEMORIAL_DAY_2026 = date(2026, 5, 25)


def main():
    # Validate using holidays.py
    is_holiday, name = is_federal_holiday(MEMORIAL_DAY_2026)
    if not is_holiday:
        print(f"ERROR: {MEMORIAL_DAY_2026} is NOT recognized as a federal holiday by holidays.py")
        print("Check backend/app/utils/holidays.py for correctness")
        sys.exit(1)

    print(f"Confirmed: {MEMORIAL_DAY_2026} is '{name}' per holidays.py")

    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    # Check current state
    cur.execute(
        "SELECT id, time_of_day, is_holiday, holiday_name FROM blocks WHERE date = %s ORDER BY time_of_day",
        (MEMORIAL_DAY_2026,),
    )
    rows = cur.fetchall()
    if not rows:
        print(f"WARNING: No blocks found for {MEMORIAL_DAY_2026}")
        conn.close()
        sys.exit(1)

    print(f"\nCurrent state ({len(rows)} slots):")
    already_flagged = True
    for block_id, tod, is_hol, hol_name in rows:
        status = "HOLIDAY" if is_hol else "not flagged"
        print(f"  {tod}: {status} (name={hol_name})")
        if not is_hol:
            already_flagged = False

    if already_flagged:
        print("\nMemorial Day already flagged. Nothing to do.")
        conn.close()
        return

    # Update
    cur.execute(
        "UPDATE blocks SET is_holiday = true, holiday_name = %s WHERE date = %s",
        (name, MEMORIAL_DAY_2026),
    )
    print(f"\nUpdated {cur.rowcount} block slots to is_holiday=true, holiday_name='{name}'")

    conn.commit()

    # Verify
    cur.execute(
        "SELECT time_of_day, is_holiday, holiday_name FROM blocks WHERE date = %s ORDER BY time_of_day",
        (MEMORIAL_DAY_2026,),
    )
    print("\nVerification:")
    for tod, is_hol, hol_name in cur.fetchall():
        print(f"  {tod}: is_holiday={is_hol}, holiday_name='{hol_name}'")

    cur.close()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
