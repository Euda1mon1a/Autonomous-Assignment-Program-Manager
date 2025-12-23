#!/usr/bin/env python3
"""
PII Sanitization Script for Residency Scheduler
================================================

Purpose:
  Sanitizes real data exports so Claude Code IDE can work with schedule data
  without exposure to PERSEC/OPSEC information.

Usage:
  python scripts/sanitize_pii.py input.json output_sanitized.json
  python scripts/sanitize_pii.py --db-export          # Sanitize from live DB
  python scripts/sanitize_pii.py --reverse mapping.json sanitized.json  # Restore

Features:
  - Replaces real names with synthetic identifiers (PGY1-01, FAC-PD, etc.)
  - Offsets dates by random amount (preserves relative timing)
  - Removes sensitive fields (deployment orders, TDY locations)
  - Creates reversible mapping file (NEVER COMMIT - gitignored)

Security:
  - Mapping files stored in .sanitize/ (gitignored)
  - Original data never modified
  - Synthetic data safe for development/AI review
"""

import argparse
import hashlib
import json
import os
import random
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# Ensure this directory is gitignored
MAPPING_DIR = Path(__file__).parent.parent / ".sanitize"
MAPPING_DIR.mkdir(exist_ok=True)

# Fields to completely remove (OPSEC/PERSEC sensitive)
REDACT_FIELDS = {
    "deployment_orders",
    "deployment_location",
    "tdy_location",
    "tdy_orders",
    "emergency_contact",
    "emergency_phone",
    "home_address",
    "personal_phone",
    "personal_email",
    "ssn",
    "social_security",
    "dod_id",
    "edipi",
}

# Fields containing names to replace
NAME_FIELDS = {
    "first_name",
    "last_name",
    "full_name",
    "name",
    "display_name",
    "supervisor_name",
    "attending_name",
    "requestor_name",
    "approver_name",
}

# Fields containing emails to sanitize
EMAIL_FIELDS = {
    "email",
    "work_email",
    "contact_email",
}


class PIISanitizer:
    """Sanitizes PII from schedule data while preserving structure."""

    def __init__(self, seed: int = None):
        """Initialize with optional seed for reproducible sanitization."""
        self.seed = seed or random.randint(1000, 9999)
        random.seed(self.seed)

        # Mapping storage
        self.name_map: dict[str, str] = {}
        self.email_map: dict[str, str] = {}
        self.date_offset: int = random.randint(-30, 30)  # Days to shift dates

        # Counters for synthetic IDs
        self.resident_counter = {"PGY-1": 1, "PGY-2": 1, "PGY-3": 1}
        self.faculty_counter = 1
        self.person_counter = 1

    def sanitize(self, data: Any) -> Any:
        """Recursively sanitize data structure."""
        if isinstance(data, dict):
            return self._sanitize_dict(data)
        elif isinstance(data, list):
            return [self.sanitize(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data

    def _sanitize_dict(self, d: dict) -> dict:
        """Sanitize a dictionary."""
        result = {}

        for key, value in d.items():
            key_lower = key.lower()

            # Completely redact sensitive fields
            if key_lower in REDACT_FIELDS:
                result[key] = "[REDACTED]"
                continue

            # Sanitize name fields
            if key_lower in NAME_FIELDS:
                result[key] = self._sanitize_name(value, d)
                continue

            # Sanitize email fields
            if key_lower in EMAIL_FIELDS:
                result[key] = self._sanitize_email(value)
                continue

            # Sanitize date fields (shift by offset)
            if key_lower.endswith("_date") or key_lower in {"date", "dob", "birth_date"}:
                result[key] = self._sanitize_date(value)
                continue

            # Recurse into nested structures
            result[key] = self.sanitize(value)

        return result

    def _sanitize_string(self, s: str) -> str:
        """Sanitize strings that might contain PII."""
        # Check for SSN patterns
        s = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', 'XXX-XX-XXXX', s)

        # Check for phone patterns
        s = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'XXX-XXX-XXXX', s)

        # Check for .mil emails
        s = re.sub(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.mil\b',
            'user@example.mil',
            s
        )

        return s

    def _sanitize_name(self, name: str, context: dict = None) -> str:
        """Replace real name with synthetic identifier."""
        if not name or name == "[REDACTED]":
            return name

        # Check if we've seen this name before
        if name in self.name_map:
            return self.name_map[name]

        # Determine role from context
        role = context.get("role", "").upper() if context else ""
        pgy_level = context.get("pgy_level") if context else None
        faculty_role = context.get("faculty_role", "") if context else ""

        # Generate synthetic ID based on role
        if role == "RESIDENT" and pgy_level:
            pgy_key = f"PGY-{pgy_level}"
            count = self.resident_counter.get(pgy_key, 1)
            synthetic = f"{pgy_key}-{count:02d}"
            self.resident_counter[pgy_key] = count + 1
        elif role == "FACULTY":
            if faculty_role:
                synthetic = f"FAC-{faculty_role.upper()}"
            else:
                synthetic = f"FAC-{self.faculty_counter:02d}"
                self.faculty_counter += 1
        else:
            synthetic = f"PERSON-{self.person_counter:03d}"
            self.person_counter += 1

        self.name_map[name] = synthetic
        return synthetic

    def _sanitize_email(self, email: str) -> str:
        """Replace real email with synthetic version."""
        if not email or email == "[REDACTED]":
            return email

        if email in self.email_map:
            return self.email_map[email]

        # Generate synthetic email
        name_part = email.split("@")[0] if "@" in email else email
        synthetic = f"user{len(self.email_map) + 1}@example.mil"

        self.email_map[email] = synthetic
        return synthetic

    def _sanitize_date(self, date_value: Any) -> Any:
        """Shift date by random offset (preserves relative timing)."""
        if not date_value:
            return date_value

        try:
            if isinstance(date_value, str):
                # Try common date formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"]:
                    try:
                        dt = datetime.strptime(date_value[:10], fmt[:10])
                        shifted = dt + timedelta(days=self.date_offset)
                        return shifted.strftime(fmt[:10])
                    except ValueError:
                        continue
            elif isinstance(date_value, (date, datetime)):
                return date_value + timedelta(days=self.date_offset)
        except Exception:
            pass

        return date_value

    def get_mapping(self) -> dict:
        """Get the mapping for potential reversal."""
        return {
            "seed": self.seed,
            "date_offset": self.date_offset,
            "names": self.name_map,
            "emails": self.email_map,
            "created_at": datetime.now().isoformat(),
        }

    def save_mapping(self, filename: str = None) -> Path:
        """Save mapping to gitignored directory."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mapping_{timestamp}.json"

        mapping_path = MAPPING_DIR / filename
        with open(mapping_path, "w") as f:
            json.dump(self.get_mapping(), f, indent=2)

        print(f"Mapping saved to: {mapping_path}")
        print(f"⚠️  NEVER COMMIT this file - it contains real→synthetic mapping")

        return mapping_path


def reverse_sanitize(mapping_path: Path, sanitized_data: dict) -> dict:
    """Reverse sanitization using mapping file (for user only)."""
    with open(mapping_path) as f:
        mapping = json.load(f)

    # Reverse the name and email maps
    reverse_names = {v: k for k, v in mapping["names"].items()}
    reverse_emails = {v: k for k, v in mapping["emails"].items()}
    date_offset = -mapping["date_offset"]  # Reverse the offset

    def reverse_recurse(data):
        if isinstance(data, dict):
            return {k: reverse_recurse(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [reverse_recurse(item) for item in data]
        elif isinstance(data, str):
            # Check if it's a synthetic name or email
            if data in reverse_names:
                return reverse_names[data]
            if data in reverse_emails:
                return reverse_emails[data]
            return data
        return data

    return reverse_recurse(sanitized_data)


def sanitize_file(input_path: Path, output_path: Path) -> Path:
    """Sanitize a JSON file."""
    with open(input_path) as f:
        data = json.load(f)

    sanitizer = PIISanitizer()
    sanitized = sanitizer.sanitize(data)

    with open(output_path, "w") as f:
        json.dump(sanitized, f, indent=2)

    mapping_path = sanitizer.save_mapping()

    print(f"✅ Sanitized data written to: {output_path}")
    print(f"📊 Stats:")
    print(f"   - Names replaced: {len(sanitizer.name_map)}")
    print(f"   - Emails replaced: {len(sanitizer.email_map)}")
    print(f"   - Date offset: {sanitizer.date_offset} days")

    return mapping_path


def main():
    parser = argparse.ArgumentParser(
        description="Sanitize PII from schedule data for safe AI review"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Input JSON file to sanitize"
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Output path for sanitized data"
    )
    parser.add_argument(
        "--reverse",
        metavar="MAPPING",
        help="Reverse sanitization using mapping file"
    )
    parser.add_argument(
        "--db-export",
        action="store_true",
        help="Export and sanitize from live database"
    )

    args = parser.parse_args()

    if args.reverse:
        if not args.input or not args.output:
            print("Usage: sanitize_pii.py --reverse mapping.json sanitized.json output.json")
            sys.exit(1)

        with open(args.input) as f:
            sanitized = json.load(f)

        restored = reverse_sanitize(Path(args.reverse), sanitized)

        with open(args.output, "w") as f:
            json.dump(restored, f, indent=2)

        print(f"✅ Restored data written to: {args.output}")
        return

    if args.db_export:
        print("Database export sanitization not yet implemented")
        print("Export your data to JSON first, then run:")
        print("  python scripts/sanitize_pii.py export.json sanitized.json")
        sys.exit(1)

    if not args.input or not args.output:
        parser.print_help()
        sys.exit(1)

    sanitize_file(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()
