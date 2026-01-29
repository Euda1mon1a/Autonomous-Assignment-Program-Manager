#!/usr/bin/env python3
"""Apply VAS and POCUS rotation activity requirements."""

from __future__ import annotations

import argparse
import os


def _load_env() -> None:
    """Load .env/.env.codex and ensure DATABASE_URL is set when possible."""
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
    parser = argparse.ArgumentParser(description="Apply VAS/POCUS requirements")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing",
    )
    args = parser.parse_args()

    _load_env()

    import uuid

    from sqlalchemy import create_engine, text

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")

    engine = create_engine(db_url)
    planned: list[tuple[str, str, str, int, int, int | None]] = []
    weeks_hash = str(uuid.uuid5(uuid.NAMESPACE_DNS, "all"))

    with engine.begin() as conn:
        activities = {
            row.code.upper(): row.id
            for row in conn.execute(
                text(
                    "SELECT id, code FROM activities "
                    "WHERE code IN ('VAS','US','FM_CLINIC') OR display_abbreviation IN ('C','VAS','US')"
                )
            )
        }
        vas_id = activities.get("VAS")
        us_id = activities.get("US")
        clinic_id = activities.get("FM_CLINIC") or activities.get("C")

        if not vas_id or not us_id or not clinic_id:
            missing = [
                name
                for name, value in {
                    "VAS": vas_id,
                    "US": us_id,
                    "FM_CLINIC": clinic_id,
                }.items()
                if value is None
            ]
            raise RuntimeError(f"Missing activities: {', '.join(missing)}")

        templates = {
            row.abbreviation.upper(): row.id
            for row in conn.execute(
                text(
                    "SELECT id, abbreviation FROM rotation_templates "
                    "WHERE abbreviation IN ('FMC','PROC','POCUS')"
                )
            )
        }
        for key in ("FMC", "PROC", "POCUS"):
            if key not in templates:
                raise RuntimeError(f"Missing rotation template: {key}")

        if not args.dry_run:
            conn.execute(
                text(
                    "UPDATE rotation_templates "
                    "SET is_archived = false "
                    "WHERE abbreviation = 'POCUS'"
                )
            )

        def upsert_req(
            template_id: str,
            template_abbrev: str,
            activity_id: str,
            activity_code: str,
            min_halfdays: int,
            max_halfdays: int,
            target_halfdays: int | None,
            priority: int,
            prefer_full_days: bool,
        ) -> None:
            result = conn.execute(
                text(
                    """
                    UPDATE rotation_activity_requirements
                    SET min_halfdays = :min_halfdays,
                        max_halfdays = :max_halfdays,
                        target_halfdays = :target_halfdays,
                        priority = :priority,
                        prefer_full_days = :prefer_full_days,
                        updated_at = now()
                    WHERE rotation_template_id = :template_id
                      AND activity_id = :activity_id
                      AND applicable_weeks IS NULL
                    RETURNING id
                    """
                ),
                {
                    "template_id": template_id,
                    "activity_id": activity_id,
                    "min_halfdays": min_halfdays,
                    "max_halfdays": max_halfdays,
                    "target_halfdays": target_halfdays,
                    "priority": priority,
                    "prefer_full_days": prefer_full_days,
                },
            ).fetchone()
            if result:
                planned.append(
                    (
                        "update",
                        template_abbrev,
                        activity_code,
                        min_halfdays,
                        max_halfdays,
                        target_halfdays,
                    )
                )
                return
            conn.execute(
                text(
                    """
                    INSERT INTO rotation_activity_requirements (
                        id,
                        rotation_template_id,
                        activity_id,
                        min_halfdays,
                        max_halfdays,
                        target_halfdays,
                        applicable_weeks,
                        applicable_weeks_hash,
                        prefer_full_days,
                        priority,
                        created_at,
                        updated_at
                    ) VALUES (
                        gen_random_uuid(),
                        :template_id,
                        :activity_id,
                        :min_halfdays,
                        :max_halfdays,
                        :target_halfdays,
                        NULL,
                        :weeks_hash,
                        :prefer_full_days,
                        :priority,
                        now(),
                        now()
                    )
                    """
                ),
                {
                    "template_id": template_id,
                    "activity_id": activity_id,
                    "min_halfdays": min_halfdays,
                    "max_halfdays": max_halfdays,
                    "target_halfdays": target_halfdays,
                    "weeks_hash": weeks_hash,
                    "prefer_full_days": prefer_full_days,
                    "priority": priority,
                },
            )
            planned.append(
                (
                    "create",
                    template_abbrev,
                    activity_code,
                    min_halfdays,
                    max_halfdays,
                    target_halfdays,
                )
            )

        for key in ("FMC", "PROC", "POCUS"):
            upsert_req(
                templates[key],
                key,
                str(vas_id),
                "VAS",
                min_halfdays=0,
                max_halfdays=1,
                target_halfdays=0,
                priority=40,
                prefer_full_days=False,
            )

        upsert_req(
            templates["POCUS"],
            "POCUS",
            str(us_id),
            "US",
            min_halfdays=1,
            max_halfdays=2,
            target_halfdays=2,
            priority=70,
            prefer_full_days=True,
        )
        upsert_req(
            templates["POCUS"],
            "POCUS",
            str(clinic_id),
            "FM_CLINIC",
            min_halfdays=1,
            max_halfdays=2,
            target_halfdays=1,
            priority=60,
            prefer_full_days=True,
        )

        if args.dry_run:
            conn.rollback()

    action = "Would apply" if args.dry_run else "Applied"
    print(f"{action} {len(planned)} requirement changes.")
    for entry in planned:
        print(
            f"{entry[0]} {entry[1]} -> {entry[2]} min={entry[3]} max={entry[4]} target={entry[5]}"
        )


if __name__ == "__main__":
    main()
