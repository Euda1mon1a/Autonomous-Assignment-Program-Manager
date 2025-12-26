"""Markdown generation for block schedule summaries.

Generates human-readable markdown files from parsed block schedules.
Output goes to docs/schedules/BLOCK_<N>_SUMMARY.md
"""

from datetime import datetime

from app.services.xlsx_import import BlockParseResult, ParsedFMITWeek


def generate_block_markdown(
    result: BlockParseResult,
    fmit_weeks: list[ParsedFMITWeek] | None = None,
    include_assignments: bool = False,
    include_special_events: bool = True,
) -> str:
    """
    Generate markdown summary of parsed block schedule.

    Args:
        result: Parsed block result from BlockScheduleParser
        fmit_weeks: Optional FMIT attending schedule
        include_assignments: If True, include daily assignment tables
        include_special_events: If True, include notes about holidays/events

    Returns:
        Markdown string formatted for docs/schedules/
    """
    lines: list[str] = []

    ***REMOVED*** Header
    lines.append(f"***REMOVED*** Block {result.block_number} Schedule Summary")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if result.start_date and result.end_date:
        lines.append(
            f"**Date Range:** {result.start_date.strftime('%B %d')} - "
            f"{result.end_date.strftime('%B %d, %Y')}"
        )
    lines.append(f"**Total Residents:** {len(result.residents)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    ***REMOVED*** Resident Roster by Template
    lines.append("***REMOVED******REMOVED*** Resident Roster")
    lines.append("")

    by_template = result.get_residents_by_template()

    ***REMOVED*** Standard resident templates first
    for template in ["R3", "R2", "R1"]:
        if template in by_template:
            residents = by_template[template]
            lines.append(f"***REMOVED******REMOVED******REMOVED*** {template} Rotation ({len(residents)} residents)")
            lines.append("")
            lines.append("| Role | Name | Confidence |")
            lines.append("|------|------|------------|")
            for r in residents:
                conf = r.get("confidence", 1.0)
                conf_indicator = (
                    "✓" if conf >= 0.9 else "⚠" if conf >= 0.8 else "✗"
                )
                lines.append(
                    f"| {r['role']} | {r['name']} | {conf:.0%} {conf_indicator} |"
                )
            lines.append("")

    ***REMOVED*** Other templates (faculty, etc.)
    other_templates = [t for t in by_template.keys() if t not in ["R3", "R2", "R1"]]
    if other_templates:
        lines.append("***REMOVED******REMOVED******REMOVED*** Other Personnel")
        lines.append("")
        for template in sorted(other_templates):
            if template:
                residents = by_template[template]
                lines.append(f"**{template}:** ({len(residents)} people)")
                lines.append("")
                for r in residents:
                    lines.append(f"- {r['name']} ({r['role']})")
                lines.append("")

    ***REMOVED*** FMIT Schedule
    if fmit_weeks:
        lines.append("---")
        lines.append("")
        lines.append("***REMOVED******REMOVED*** FMIT Attending Schedule")
        lines.append("")
        lines.append("| Week | Dates | Faculty | Holiday |")
        lines.append("|------|-------|---------|---------|")
        for f in fmit_weeks:
            dates = (
                f"{f.start_date} - {f.end_date}"
                if f.start_date
                else "TBD"
            )
            holiday = "⭐" if f.is_holiday_call else ""
            lines.append(
                f"| {f.week_number} | {dates} | {f.faculty_name} | {holiday} |"
            )
        lines.append("")

    ***REMOVED*** Special Events (hardcoded for Block 10 as example)
    if include_special_events and result.block_number == 10:
        lines.append("---")
        lines.append("")
        lines.append("***REMOVED******REMOVED*** Special Events")
        lines.append("")
        lines.append("| Date | Event | Impact |")
        lines.append("|------|-------|--------|")
        lines.append("| Mar 12-14 | USAFP Conference | Resident call coverage |")
        lines.append("| Mar 27-29 | OB Retreat | Coverage swaps needed |")
        lines.append("| Mar 30 | Doctors' Day | Special recognition |")
        lines.append("| Apr 5 | Easter | Federal holiday |")
        lines.append("")

    ***REMOVED*** Warnings
    if result.warnings:
        lines.append("---")
        lines.append("")
        lines.append("***REMOVED******REMOVED*** Parsing Warnings")
        lines.append("")
        for w in result.warnings:
            lines.append(f"- ⚠ {w}")
        lines.append("")

    ***REMOVED*** Errors
    if result.errors:
        lines.append("---")
        lines.append("")
        lines.append("***REMOVED******REMOVED*** Parsing Errors")
        lines.append("")
        for e in result.errors:
            lines.append(f"- ❌ {e}")
        lines.append("")

    ***REMOVED*** Optional daily assignments
    if include_assignments and result.assignments:
        lines.append("---")
        lines.append("")
        lines.append("***REMOVED******REMOVED*** Daily Assignments")
        lines.append("")

        ***REMOVED*** Group by date
        by_date: dict = {}
        for a in result.assignments:
            date_key = a.date
            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append(a)

        for date_key in sorted(by_date.keys()):
            assignments = by_date[date_key]
            lines.append(f"***REMOVED******REMOVED******REMOVED*** {date_key.strftime('%A, %B %d')}")
            lines.append("")
            lines.append("| Person | Template | AM | PM |")
            lines.append("|--------|----------|----|----|")
            for a in assignments:
                lines.append(
                    f"| {a.person_name} | {a.template} | "
                    f"{a.slot_am or '-'} | {a.slot_pm or '-'} |"
                )
            lines.append("")

    ***REMOVED*** Footer
    lines.append("---")
    lines.append("")
    lines.append(
        "*Generated by BlockScheduleParser - "
        "anchor-based fuzzy-tolerant Excel parsing*"
    )
    lines.append("")

    return "\n".join(lines)


def write_block_markdown(
    result: BlockParseResult,
    output_dir: str = "docs/schedules",
    fmit_weeks: list[ParsedFMITWeek] | None = None,
) -> str:
    """
    Generate and write block markdown to file.

    Args:
        result: Parsed block result
        output_dir: Output directory (default: docs/schedules)
        fmit_weeks: Optional FMIT schedule

    Returns:
        Path to written file
    """
    from pathlib import Path

    ***REMOVED*** Ensure directory exists
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    ***REMOVED*** Generate filename
    filename = f"BLOCK_{result.block_number}_SUMMARY.md"
    filepath = out_path / filename

    ***REMOVED*** Generate and write markdown
    content = generate_block_markdown(result, fmit_weeks=fmit_weeks)
    filepath.write_text(content)

    return str(filepath)
