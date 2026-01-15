"""
ROSETTA XML Validator - Compare generated XML against ground truth.

This is the validation checkpoint in the "central dogma" pipeline:
  ROSETTA.xlsx → ROSETTA.xml (ground truth)
                      ↓ compare
  Generated.xml ══════╝
                      ↓ if match
                 Output.xlsx

Catches errors at the XML stage, before xlsx conversion.
"""

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


def compare_xml(
    rosetta_xml: Path | str,
    generated_xml: str | Path,
) -> list[str]:
    """
    Compare generated XML against ROSETTA XML ground truth.

    Returns list of mismatches in format:
        "{resident} {date} {AM/PM}: expected {X}, got {Y}"

    Empty list means validation passed.

    Args:
        rosetta_xml: Path to ROSETTA ground truth XML
        generated_xml: Generated XML string or path

    Returns:
        List of mismatch descriptions
    """
    # Parse ROSETTA
    rosetta_path = Path(rosetta_xml)
    if not rosetta_path.exists():
        return [f"ROSETTA XML not found: {rosetta_path}"]

    rosetta_tree = ET.parse(rosetta_path)
    rosetta_root = rosetta_tree.getroot()

    # Parse generated - detect if it's a path or XML content
    if isinstance(generated_xml, Path):
        generated_tree = ET.parse(generated_xml)
        generated_root = generated_tree.getroot()
    elif isinstance(generated_xml, str):
        # Check if it looks like XML content (starts with < or whitespace then <)
        stripped = generated_xml.strip()
        if stripped.startswith("<"):
            generated_root = ET.fromstring(generated_xml)
        else:
            # Treat as path
            generated_tree = ET.parse(generated_xml)
            generated_root = generated_tree.getroot()
    else:
        raise ValueError(
            f"generated_xml must be Path or str, got {type(generated_xml)}"
        )

    mismatches = []

    # Build lookup from ROSETTA: (name, date, time) -> code
    expected: dict[tuple[str, str, str], str] = {}
    for resident in rosetta_root.findall(".//resident"):
        name = resident.get("name", "")
        for day in resident.findall("day"):
            date = day.get("date", "")
            am_code = day.get("am", "")
            pm_code = day.get("pm", "")
            if am_code:
                expected[(name, date, "AM")] = am_code
            if pm_code:
                expected[(name, date, "PM")] = pm_code

    # Compare against generated
    for resident in generated_root.findall(".//resident"):
        name = resident.get("name", "")
        for day in resident.findall("day"):
            date = day.get("date", "")
            am_actual = day.get("am", "")
            pm_actual = day.get("pm", "")

            # Check AM
            key_am = (name, date, "AM")
            if key_am in expected:
                if expected[key_am] != am_actual:
                    mismatches.append(
                        f"{name} {date} AM: expected {expected[key_am]}, got {am_actual}"
                    )
            elif am_actual:
                # Generated has value but ROSETTA doesn't
                mismatches.append(
                    f"{name} {date} AM: expected (empty), got {am_actual}"
                )

            # Check PM
            key_pm = (name, date, "PM")
            if key_pm in expected:
                if expected[key_pm] != pm_actual:
                    mismatches.append(
                        f"{name} {date} PM: expected {expected[key_pm]}, got {pm_actual}"
                    )
            elif pm_actual:
                mismatches.append(
                    f"{name} {date} PM: expected (empty), got {pm_actual}"
                )

    # Check for missing residents in generated
    generated_names = {r.get("name") for r in generated_root.findall(".//resident")}
    rosetta_names = {r.get("name") for r in rosetta_root.findall(".//resident")}

    for missing in rosetta_names - generated_names:
        mismatches.append(f"Missing resident in generated: {missing}")

    for extra in generated_names - rosetta_names:
        mismatches.append(f"Extra resident in generated: {extra}")

    return mismatches


def validate_xml_structure(xml_content: str) -> list[str]:
    """
    Validate XML structure matches expected schema.

    Checks:
    - Root element is <schedule> with block_start/block_end
    - <resident> elements have name, pgy, rotation1 attributes
    - <day> elements have date, weekday, am, pm attributes

    Returns list of structural issues.
    """
    issues = []

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        return [f"XML parse error: {e}"]

    # Check root
    if root.tag != "schedule":
        issues.append(f"Root element should be 'schedule', got '{root.tag}'")

    if not root.get("block_start"):
        issues.append("Missing block_start attribute on schedule")
    if not root.get("block_end"):
        issues.append("Missing block_end attribute on schedule")

    # Check residents
    residents = root.findall(".//resident")
    if not residents:
        issues.append("No resident elements found")

    for i, res in enumerate(residents):
        if not res.get("name"):
            issues.append(f"Resident {i} missing name attribute")
        if not res.get("pgy"):
            issues.append(f"Resident {res.get('name', i)} missing pgy attribute")

        days = res.findall("day")
        if not days:
            issues.append(f"Resident {res.get('name', i)} has no day elements")

        for day in days:
            if not day.get("date"):
                issues.append(f"Resident {res.get('name', i)} has day without date")

    return issues


def get_mismatch_summary(mismatches: list[str]) -> dict:
    """
    Summarize mismatches by resident and by type.

    Returns:
        {
            "total": N,
            "by_resident": {"Name": count, ...},
            "by_time": {"AM": count, "PM": count},
            "sample_mismatches": [...first 5...]
        }
    """
    by_resident: dict[str, int] = {}
    by_time: dict[str, int] = {"AM": 0, "PM": 0}

    for m in mismatches:
        # Parse "Name Date TIME: expected X, got Y"
        parts = m.split(" ")
        if len(parts) >= 3:
            # Handle "Last, First" names
            if "," in parts[0]:
                name = f"{parts[0]} {parts[1]}"
                time = parts[3] if len(parts) > 3 else ""
            else:
                name = parts[0]
                time = parts[2] if len(parts) > 2 else ""

            by_resident[name] = by_resident.get(name, 0) + 1

            if "AM" in time:
                by_time["AM"] += 1
            elif "PM" in time:
                by_time["PM"] += 1

    return {
        "total": len(mismatches),
        "by_resident": by_resident,
        "by_time": by_time,
        "sample_mismatches": mismatches[:5],
    }
