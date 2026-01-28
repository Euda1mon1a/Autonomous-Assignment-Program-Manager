#!/usr/bin/env python3
"""Apply inpatient time-off weekly patterns from a JSON override file."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def _load_env() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return

    for path in (".env.codex", ".env"):
        if os.path.exists(path):
            load_dotenv(path, override=True)

    if not os.environ.get("DATABASE_URL"):
        pwd = os.environ.get("DB_PASSWORD")
        if pwd:
            os.environ["DATABASE_URL"] = (
                f"postgresql://scheduler:{pwd}@localhost:5432/residency_scheduler"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply inpatient time-off overrides")
    parser.add_argument(
        "--input",
        action="append",
        default=None,
        help="Override JSON file (repeatable). Defaults to data/inpatient_time_off_overrides.json and data/inpatient_time_off_overrides_manual.json when present.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing",
    )
    args = parser.parse_args()

    _load_env()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")

    input_paths: list[Path]
    if args.input:
        input_paths = [Path(p) for p in args.input]
    else:
        input_paths = [
            Path("data/inpatient_time_off_overrides.json"),
            Path("data/inpatient_time_off_overrides_manual.json"),
        ]
        input_paths = [p for p in input_paths if p.exists()]
        if not input_paths:
            raise RuntimeError("No override files found")

    from sqlalchemy import create_engine, text

    engine = create_engine(db_url)
    planned = []

    with engine.begin() as conn:
        activity_rows = conn.execute(
            text(
                "SELECT id, code FROM activities WHERE UPPER(code) IN ('OFF','W')"
            )
        ).fetchall()
        activities = {row.code.upper(): row.id for row in activity_rows}
        off_id = activities.get("OFF")
        w_id = activities.get("W")
        if not off_id or not w_id:
            raise RuntimeError("Missing OFF or W activity")

        desired_by_template: dict[str, set[tuple[int, int, str]]] = {}

        for input_path in input_paths:
            if not input_path.exists():
                raise RuntimeError(f"Override file not found: {input_path}")
            payload = json.loads(input_path.read_text())
            patterns = payload.get("patterns", {})
            key_type = payload.get("key_type", "template_display_abbreviation")
            note_prefix = payload.get("source", input_path.name)
            override_mode = payload.get("override_mode", "").strip().lower()

            if key_type not in (
                "template_display_abbreviation",
                "template_abbreviation",
            ):
                raise RuntimeError(f"Unsupported key_type: {key_type}")

            for key, entries in patterns.items():
                key_value = key.strip().upper()
                if key_type == "template_display_abbreviation":
                    templates = conn.execute(
                        text(
                            "SELECT id, display_abbreviation, abbreviation FROM rotation_templates "
                            "WHERE UPPER(display_abbreviation) = :display"
                        ),
                        {"display": key_value},
                    ).fetchall()
                else:
                    templates = conn.execute(
                        text(
                            "SELECT id, display_abbreviation, abbreviation FROM rotation_templates "
                            "WHERE UPPER(abbreviation) = :abbrev"
                        ),
                        {"abbrev": key_value},
                    ).fetchall()

                if not templates:
                    planned.append(("missing_template", key_type, key_value))
                    continue

                for tmpl in templates:
                    template_id = tmpl.id
                    if override_mode == "replace":
                        desired_by_template[template_id] = set()
                    for entry in entries:
                        week = entry["week"]
                        dow = entry["day_of_week"]
                        tod = entry["time_of_day"]
                        code = str(entry["code"]).upper()
                        activity_id = off_id if code == "OFF" else w_id
                        activity_type = code.lower()
                        label = entry.get("row_label", "").strip()
                        note = (
                            f"Templates sheet import ({label})"
                            if label
                            else f"Time-off override ({note_prefix})"
                        )

                        desired_by_template.setdefault(template_id, set()).add(
                            (int(week), int(dow), str(tod).upper())
                        )

                        if args.dry_run:
                            planned.append(
                                (
                                    "upsert",
                                    key_type,
                                    key_value,
                                    week,
                                    dow,
                                    tod,
                                    code,
                                )
                            )
                            continue

                        updated = conn.execute(
                            text(
                                """
                                UPDATE weekly_patterns
                                   SET activity_id = :activity_id,
                                       activity_type = :activity_type,
                                       notes = :notes,
                                       updated_at = now()
                                 WHERE rotation_template_id = :template_id
                                   AND day_of_week = :day_of_week
                                   AND time_of_day = :time_of_day
                                   AND week_number = :week_number
                                """
                            ),
                            {
                                "activity_id": activity_id,
                                "activity_type": activity_type,
                                "notes": note,
                                "template_id": template_id,
                                "day_of_week": dow,
                                "time_of_day": tod,
                                "week_number": week,
                            },
                        ).rowcount

                        if updated:
                            planned.append(
                                (
                                    "update",
                                    key_type,
                                    key_value,
                                    week,
                                    dow,
                                    tod,
                                    code,
                                )
                            )
                            continue

                        conn.execute(
                            text(
                                """
                                INSERT INTO weekly_patterns (
                                    id,
                                    rotation_template_id,
                                    day_of_week,
                                    time_of_day,
                                    week_number,
                                    activity_type,
                                    activity_id,
                                    is_protected,
                                    notes,
                                    created_at,
                                    updated_at
                                ) VALUES (
                                    gen_random_uuid(),
                                    :template_id,
                                    :day_of_week,
                                    :time_of_day,
                                    :week_number,
                                    :activity_type,
                                    :activity_id,
                                    false,
                                    :notes,
                                    now(),
                                    now()
                                )
                                """
                            ),
                            {
                                "template_id": template_id,
                                "day_of_week": dow,
                                "time_of_day": tod,
                                "week_number": week,
                                "activity_type": activity_type,
                                "activity_id": activity_id,
                                "notes": note,
                            },
                        )
                        planned.append(
                            (
                                "insert",
                                key_type,
                                key_value,
                                week,
                                dow,
                                tod,
                                code,
                            )
                        )

        # Remove time-off slots that are not in the desired set for a template
        for template_id, desired_slots in desired_by_template.items():
            rows = conn.execute(
                text(
                    """
                    SELECT wp.id, wp.week_number, wp.day_of_week, wp.time_of_day, a.code
                    FROM weekly_patterns wp
                    JOIN activities a ON a.id = wp.activity_id
                    WHERE wp.rotation_template_id = :template_id
                      AND UPPER(a.code) IN ('OFF','W')
                    """
                ),
                {"template_id": template_id},
            ).fetchall()

            for row in rows:
                slot = (int(row.week_number or 0), int(row.day_of_week), row.time_of_day)
                if slot in desired_slots:
                    continue
                if args.dry_run:
                    planned.append(("delete", template_id, row.week_number, row.day_of_week, row.time_of_day, row.code))
                    continue
                conn.execute(
                    text("DELETE FROM weekly_patterns WHERE id = :id"),
                    {"id": row.id},
                )
                planned.append(("delete", template_id, row.week_number, row.day_of_week, row.time_of_day, row.code))

    for entry in planned:
        print(entry)


if __name__ == "__main__":
    main()
