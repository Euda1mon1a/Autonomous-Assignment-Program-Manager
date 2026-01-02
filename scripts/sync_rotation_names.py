#!/usr/bin/env python3
"""
Sync rotation template names with authoritative CSV abbreviations.

This script compares database rotation_templates with the user's authoritative
CSV file containing correct medical abbreviation definitions, then updates
any mismatched names.

Usage:
    # Dry run - show what would change
    python scripts/sync_rotation_names.py --csv /path/to/abbreviations.csv --dry-run

    # Apply changes
    python scripts/sync_rotation_names.py --csv /path/to/abbreviations.csv

    # Verbose mode shows all comparisons
    python scripts/sync_rotation_names.py --csv /path/to/abbreviations.csv --verbose
"""
import argparse
import csv
import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.db.session import SessionLocal
from app.models.rotation_template import RotationTemplate


def load_csv_mappings(csv_path: str) -> dict[str, dict]:
    """
    Load abbreviation mappings from CSV file.

    Args:
        csv_path: Path to the CSV file with columns:
                  abbreviation, full_meaning, category, description, frequency, percentage, notes

    Returns:
        Dictionary mapping abbreviation -> {full_meaning, category, description}
    """
    mappings = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Skip header row if it's the title
        first_line = f.readline()
        if 'abbreviation' not in first_line.lower():
            f.seek(0)  # Reset if first line isn't header

        reader = csv.DictReader(f)
        for row in reader:
            abbrev = row.get('abbreviation', '').strip()
            if abbrev:
                mappings[abbrev] = {
                    'full_meaning': row.get('full_meaning', '').strip(),
                    'category': row.get('category', '').strip(),
                    'description': row.get('description', '').strip(),
                }
    return mappings


def extract_base_abbreviation(db_abbrev: str) -> tuple[str, str]:
    """
    Extract base abbreviation from DB format.

    Examples:
        'CLI-AM' -> ('CLI', 'AM')
        'FMIT-PM' -> ('FMIT', 'PM')
        'NF-NICU' -> ('NF', 'NICU')
        'LDNF' -> ('LDNF', '')
        'ICU' -> ('ICU', '')

    Returns:
        Tuple of (base_abbreviation, suffix)
    """
    # Common time-of-day suffixes
    tod_suffixes = ['-AM', '-PM']
    for suffix in tod_suffixes:
        if db_abbrev.endswith(suffix):
            return db_abbrev[:-len(suffix)], suffix[1:]  # Remove leading hyphen from suffix

    # Check for combined rotations (e.g., NF-NICU, NF-DERM)
    if '-' in db_abbrev:
        parts = db_abbrev.split('-', 1)
        return parts[0], parts[1]

    return db_abbrev, ''


def build_expected_name(csv_mapping: dict, base_abbrev: str, suffix: str, db_abbrev: str) -> str | None:
    """
    Build expected full name from CSV mapping.

    Args:
        csv_mapping: The CSV row data for the base abbreviation
        base_abbrev: Base abbreviation (e.g., 'CLI', 'FMIT')
        suffix: Suffix if any (e.g., 'AM', 'PM', 'NICU')
        db_abbrev: Original database abbreviation

    Returns:
        Expected full name, or None if can't determine
    """
    full_meaning = csv_mapping.get('full_meaning', '')
    if not full_meaning:
        return None

    # Handle time-of-day suffixes
    if suffix in ('AM', 'PM'):
        return f"{full_meaning} {suffix}"

    # Handle combined rotations (e.g., NF-NICU -> Night Float + NICU)
    if suffix:
        # suffix is actually another abbreviation
        return None  # Too complex to auto-generate

    return full_meaning


def apply_known_fixes() -> list[tuple[str, str, str]]:
    """
    Return list of known fixes based on manual CSV analysis.

    These are cases where the DB abbreviation doesn't directly map
    to a CSV abbreviation, but we know the correct name.

    Returns:
        List of (abbreviation, current_name_pattern, correct_name) tuples
    """
    return [
        # Abbreviation, pattern to match (for safety), correct name
        ('ICU', 'Intern', 'Intensive Care Unit'),
        ('LAD', 'Intern', 'Labor and Delivery'),
        ('IM-INT', 'Internal Medicine', 'Internal Medicine Ward Intern'),
        ('PEDS-W', 'Pediatrics', 'Pediatric Ward Intern'),
        ('PC', 'Recovery', 'Post Call'),
    ]


def sync_rotation_names(
    csv_path: str,
    dry_run: bool = False,
    verbose: bool = False
) -> tuple[int, int, list[dict]]:
    """
    Sync rotation template names with CSV mappings.

    Args:
        csv_path: Path to authoritative CSV file
        dry_run: If True, don't make changes
        verbose: If True, print all comparisons

    Returns:
        Tuple of (updated_count, skipped_count, changes_made)
    """
    db = SessionLocal()
    updated = 0
    skipped = 0
    changes = []

    try:
        # Load CSV mappings
        csv_mappings = load_csv_mappings(csv_path)
        print(f"Loaded {len(csv_mappings)} abbreviation mappings from CSV")

        # Get all rotation templates
        templates = db.query(RotationTemplate).order_by(RotationTemplate.abbreviation).all()
        print(f"Found {len(templates)} rotation templates in database\n")

        # Apply known fixes first
        known_fixes = apply_known_fixes()
        for abbrev, pattern, correct_name in known_fixes:
            template = db.query(RotationTemplate).filter(
                RotationTemplate.abbreviation == abbrev
            ).first()

            if template and pattern in template.name and template.name != correct_name:
                old_name = template.name
                if not dry_run:
                    template.name = correct_name
                changes.append({
                    'abbreviation': abbrev,
                    'old_name': old_name,
                    'new_name': correct_name,
                    'source': 'known_fix'
                })
                updated += 1
                print(f"  FIX: {abbrev}")
                print(f"       Old: {old_name}")
                print(f"       New: {correct_name}")

        # Check for additional mismatches based on CSV
        for template in templates:
            base_abbrev, suffix = extract_base_abbreviation(template.abbreviation)

            # Skip if already processed by known fixes
            if any(c['abbreviation'] == template.abbreviation for c in changes):
                continue

            # Look for direct match in CSV
            if base_abbrev in csv_mappings:
                expected = build_expected_name(
                    csv_mappings[base_abbrev],
                    base_abbrev,
                    suffix,
                    template.abbreviation
                )

                if expected and template.name != expected:
                    # Check if it's a significant difference (not just suffix)
                    csv_meaning = csv_mappings[base_abbrev]['full_meaning']
                    if csv_meaning.lower() not in template.name.lower():
                        if verbose:
                            print(f"  MISMATCH: {template.abbreviation}")
                            print(f"       DB:  {template.name}")
                            print(f"       CSV: {expected}")
                        skipped += 1  # Don't auto-fix, just report
                elif verbose:
                    print(f"  OK: {template.abbreviation} = {template.name}")
            elif verbose:
                print(f"  NO CSV: {template.abbreviation} = {template.name}")

        if not dry_run:
            db.commit()
            print(f"\nCommitted {updated} changes to database")
        else:
            print(f"\n[DRY RUN] Would update {updated} rotation templates")

        if skipped > 0:
            print(f"Skipped {skipped} potential mismatches (review manually)")

    finally:
        db.close()

    return updated, skipped, changes


def main():
    parser = argparse.ArgumentParser(
        description="Sync rotation template names with authoritative CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would change
  python scripts/sync_rotation_names.py --csv ~/Desktop/medical_abbreviations.csv --dry-run

  # Apply changes
  python scripts/sync_rotation_names.py --csv ~/Desktop/medical_abbreviations.csv

  # Verbose mode shows all comparisons
  python scripts/sync_rotation_names.py --csv ~/Desktop/medical_abbreviations.csv -v
        """
    )

    parser.add_argument(
        "--csv",
        required=True,
        help="Path to authoritative CSV file with abbreviation mappings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without making changes"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all comparisons, not just changes"
    )

    args = parser.parse_args()

    # Validate CSV exists
    if not Path(args.csv).exists():
        print(f"Error: CSV file not found: {args.csv}")
        sys.exit(1)

    if args.dry_run:
        print("=== DRY RUN MODE ===\n")

    updated, skipped, changes = sync_rotation_names(
        csv_path=args.csv,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Updated: {updated}")
    print(f"Skipped (review manually): {skipped}")

    if changes:
        print("\nChanges made:")
        for c in changes:
            print(f"  {c['abbreviation']}: {c['old_name']} -> {c['new_name']}")


if __name__ == "__main__":
    main()
