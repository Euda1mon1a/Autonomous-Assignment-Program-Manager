#!/usr/bin/env python3
"""
Audit activity supervision metadata in the local database.

Flags:
- Clinical activities missing requires_supervision
- Supervision providers (AT/PCAT/DO/SM) and any non-clinical providers

Usage:
    python3.11 scripts/ops/supervision_activity_audit.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def _load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return

    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        key = key.strip()
        if key == "CORS_ORIGINS":
            if not os.environ.get(key) or '"' not in os.environ.get(key, ""):
                os.environ[key] = value
            continue
        if key not in os.environ:
            os.environ[key] = value

    if not os.environ.get("DATABASE_URL") and os.environ.get("DB_PASSWORD"):
        os.environ["DATABASE_URL"] = (
            f"postgresql://scheduler:{os.environ['DB_PASSWORD']}@localhost:5432/"
            "residency_scheduler"
        )


_load_env()

from app.db.session import SessionLocal  # noqa: E402
from app.models.activity import Activity  # noqa: E402


def main() -> int:
    _load_env()
    session = SessionLocal()
    try:
        activities = session.query(Activity).filter(Activity.is_archived == False).all()
    finally:
        session.close()

    clinical_missing = [
        a for a in activities
        if a.activity_category == "clinical" and not a.requires_supervision
    ]
    providers = [a for a in activities if a.provides_supervision]
    nonclinical_providers = [
        a for a in providers if a.activity_category != "clinical"
    ]

    print("Supervision Activity Audit")
    print("===========================")
    print(f"Total active activities: {len(activities)}")
    print(f"Clinical missing requires_supervision: {len(clinical_missing)}")
    if clinical_missing:
        print("  -", ", ".join(sorted({a.code or a.name for a in clinical_missing})))
    print(f"Provides supervision: {len(providers)}")
    if providers:
        print("  -", ", ".join(sorted({a.code or a.name for a in providers})))
    print(f"Non-clinical providers: {len(nonclinical_providers)}")
    if nonclinical_providers:
        print("  -", ", ".join(sorted({a.code or a.name for a in nonclinical_providers})))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
