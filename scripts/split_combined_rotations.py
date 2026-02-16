#!/usr/bin/env python3
"""Split combined rotation assignments (e.g., NF+DERM) into separate half-block assignments."""

import psycopg2
from uuid import uuid4
from datetime import timedelta

DB_URL = "postgresql://scheduler:5XcUhOacvejEwBWW9M8BpSjlkrhzAxtt@db:5432/residency_scheduler"

# Template IDs for splitting
COMBINED_TEMPLATES = {
    # template_id: (first_half_template_name, second_half_template_name)
    "38d35ac5-bb3c-4161-ace8-9f26ec4e88a6": ("Night Float", "Dermatology"),  # NF-DERM
    "6dd781d5-41aa-4dd3-a44b-a3c3eea439c5": ("Night Float", "FMIT"),          # NF-I (Night Float Intern + FMIT)
    "691ad20d-cc4a-4d2a-bed4-22b90ad1a903": ("Night Float", "Cardiology"),    # NF+ (Night Float + Cardiology)
}


def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Get template IDs for individual rotations
    cur.execute("""
        SELECT id, name FROM rotation_templates
        WHERE name IN ('Night Float AM', 'Night Float PM', 'Dermatology', 'Cardiology',
                       'Family Medicine Inpatient Team Resident', 'Post-Call Recovery',
                       'FMIT AM', 'FMIT PM')
    """)
    templates = {row[1]: row[0] for row in cur.fetchall()}

    print("Templates found:")
    for name, tid in templates.items():
        print(f"  {name}: {tid}")

    # Map logical names to actual template IDs
    template_map = {
        "Night Float": {
            "AM": templates.get("Night Float AM"),
            "PM": templates.get("Night Float PM"),
        },
        "Dermatology": {
            "AM": templates.get("Dermatology"),  # Same for AM and PM
            "PM": templates.get("Dermatology"),
        },
        "Cardiology": {
            "AM": templates.get("Cardiology"),
            "PM": templates.get("Cardiology"),
        },
        "FMIT": {
            "AM": templates.get("FMIT AM") or templates.get("Family Medicine Inpatient Team Resident"),
            "PM": templates.get("FMIT PM") or templates.get("Family Medicine Inpatient Team Resident"),
        },
        "PC": {
            "AM": templates.get("Post-Call Recovery"),
            "PM": templates.get("Post-Call Recovery"),
        },
    }

    print("\nTemplate map:")
    for name, ids in template_map.items():
        print(f"  {name}: AM={ids.get('AM')}, PM={ids.get('PM')}")

    # Find all combined assignments
    cur.execute("""
        SELECT a.id, a.person_id, a.block_id, a.rotation_template_id,
               b.block_number, b.date, b.time_of_day,
               p.name as person_name, rt.name as rotation_name
        FROM assignments a
        JOIN blocks b ON a.block_id = b.id
        JOIN people p ON a.person_id = p.id
        JOIN rotation_templates rt ON a.rotation_template_id = rt.id
        WHERE a.rotation_template_id IN %s
          AND b.block_number IN (10, 11, 12, 13)
        ORDER BY p.name, b.block_number, b.date, b.time_of_day
    """, (tuple(COMBINED_TEMPLATES.keys()),))

    combined_assignments = cur.fetchall()
    print(f"\nFound {len(combined_assignments)} combined assignments to split")

    # Group by person + block
    grouped = {}
    for row in combined_assignments:
        a_id, person_id, block_id, rot_id, block_num, block_date, time_of_day, person_name, rot_name = row
        key = (person_id, block_num, rot_id)
        if key not in grouped:
            grouped[key] = {
                "person_id": person_id,
                "person_name": person_name,
                "block_number": block_num,
                "rotation_name": rot_name,
                "rotation_id": rot_id,
                "assignments": []
            }
        grouped[key]["assignments"].append({
            "id": a_id,
            "block_id": block_id,
            "date": block_date,
            "time_of_day": time_of_day,
        })

    print(f"\nGrouped into {len(grouped)} person-block combinations")

    # Process each group
    total_deleted = 0
    total_created = 0

    for key, group in grouped.items():
        person_id = group["person_id"]
        person_name = group["person_name"]
        block_number = group["block_number"]
        rot_name = group["rotation_name"]
        rot_id = group["rotation_id"]
        assignments = group["assignments"]

        print(f"\nProcessing: {person_name} - Block {block_number} - {rot_name}")

        # Get the split mapping
        first_rot, second_rot = COMBINED_TEMPLATES[rot_id]
        print(f"  Split: {first_rot} (half 1) -> PC (day 15) -> {second_rot} (half 2)")

        # Sort assignments by date
        assignments.sort(key=lambda x: (x["date"], x["time_of_day"]))

        # Find the midpoint date (day 15 is start of second half)
        first_date = assignments[0]["date"]
        mid_date = first_date + timedelta(days=14)  # Day 15 is 14 days after day 1

        print(f"  Block starts: {first_date}, Mid-block (day 15): {mid_date}")

        # Delete original combined assignments
        assignment_ids = [a["id"] for a in assignments]
        cur.execute("DELETE FROM assignments WHERE id IN %s", (tuple(assignment_ids),))
        total_deleted += len(assignment_ids)
        print(f"  Deleted {len(assignment_ids)} combined assignments")

        # Create new split assignments
        new_count = 0
        for a in assignments:
            block_id = a["block_id"]
            block_date = a["date"]
            time_of_day = a["time_of_day"]

            if block_date < mid_date:
                # First half: Night Float
                rot_template_id = template_map[first_rot][time_of_day]
            elif block_date == mid_date:
                # Day 15: Post-Call Recovery
                rot_template_id = template_map["PC"][time_of_day]
            else:
                # Second half (day 16+): The other rotation
                rot_template_id = template_map[second_rot][time_of_day]

            if rot_template_id:
                cur.execute("""
                    INSERT INTO assignments (id, person_id, block_id, rotation_template_id, role, created_by, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 'primary', 'admin', NOW(), NOW())
                """, (str(uuid4()), person_id, block_id, rot_template_id))
                new_count += 1

        total_created += new_count
        print(f"  Created {new_count} new assignments")

    conn.commit()
    print(f"\n=== Summary ===")
    print(f"Deleted: {total_deleted} combined assignments")
    print(f"Created: {total_created} split assignments")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
