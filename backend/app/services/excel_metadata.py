"""Excel metadata utility for stateful round-trips."""

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from typing import Any, Optional
from uuid import UUID

from openpyxl import Workbook
from openpyxl.workbook.defined_name import DefinedName


@dataclass
class ExportMetadata:
    """Metadata blob for exported Excel files."""

    academic_year: int
    export_timestamp: str
    block_number: int | None = None  # Optional for year-level
    export_version: int = 1
    block_map: dict[str, str] | None = None  # sheet_name -> block_uuid
    llm_rules_of_engagement: str | None = (
        None  # AI agent instructions embedded in the workbook
    )

    def to_json(self) -> str:
        """Convert metadata to JSON string."""
        d = asdict(self)
        # Clean up nulls for cleaner JSON
        return json.dumps({k: v for k, v in d.items() if v is not None})

    @classmethod
    def from_json(cls, data: str) -> "ExportMetadata":
        """Load metadata from JSON string."""
        return cls(**json.loads(data))


def write_sys_meta_sheet(wb: Workbook, meta: ExportMetadata) -> None:
    """
    Create a veryHidden sheet __SYS_META__ with metadata JSON.

    veryHidden sheets cannot be unhidden via the Excel UI.
    """
    if "__SYS_META__" in wb.sheetnames:
        del wb["__SYS_META__"]
    ws = wb.create_sheet("__SYS_META__")
    ws.sheet_state = "veryHidden"
    ws.cell(row=1, column=1, value=meta.to_json())


def read_sys_meta(wb: Workbook) -> ExportMetadata | None:
    """Read metadata from __SYS_META__ sheet if present."""
    if "__SYS_META__" not in wb.sheetnames:
        return None
    ws = wb["__SYS_META__"]
    val = ws.cell(row=1, column=1).value
    if not val:
        return None
    try:
        return ExportMetadata.from_json(str(val))
    except Exception:
        return None


def write_ref_sheet(
    wb: Workbook, rotation_codes: list[str], activity_codes: list[str]
) -> None:
    """
    Create a veryHidden sheet __REF__ with Named Ranges for validation.

    Named Ranges:
    - ValidRotations: range of valid rotation abbreviations
    - ValidActivities: range of valid activity codes
    """
    if "__REF__" in wb.sheetnames:
        del wb["__REF__"]
    ws = wb.create_sheet("__REF__")
    ws.sheet_state = "veryHidden"

    # Header
    ws.cell(row=1, column=1, value="ValidRotations")
    ws.cell(row=1, column=2, value="ValidActivities")

    # Data
    sorted_rotations = sorted(set(code for code in rotation_codes if code))
    sorted_activities = sorted(set(code for code in activity_codes if code))

    for i, code in enumerate(sorted_rotations, start=2):
        ws.cell(row=i, column=1, value=code)

    for i, code in enumerate(sorted_activities, start=2):
        ws.cell(row=i, column=2, value=code)

    # Named Ranges using DefinedName
    # ValidRotations: Col A
    rot_range = f"'{ws.title}'!$A$2:$A${max(2, len(sorted_rotations) + 1)}"
    wb.defined_names.add(DefinedName("ValidRotations", attr_text=rot_range))

    # ValidActivities: Col B
    act_range = f"'{ws.title}'!$B$2:$B${max(2, len(sorted_activities) + 1)}"
    wb.defined_names.add(DefinedName("ValidActivities", attr_text=act_range))


def read_ref_codes(wb: Workbook) -> dict[str, list[str]]:
    """Read reference codes from __REF__ sheet."""
    res = {"rotations": [], "activities": []}
    if "__REF__" not in wb.sheetnames:
        return res

    ws = wb["__REF__"]

    # Read rotations (Col A)
    i = 2
    while True:
        val = ws.cell(row=i, column=1).value
        if not val:
            break
        res["rotations"].append(str(val))
        i += 1

    # Read activities (Col B)
    i = 2
    while True:
        val = ws.cell(row=i, column=2).value
        if not val:
            break
        res["activities"].append(str(val))
        i += 1

    return res


def normalize_for_hash(val: Any) -> str:
    """Aggressively normalize cell values for symmetric export/import hashes.

    Excel may coerce types (e.g. "1.0" for integer 1), add trailing spaces,
    or change case. This ensures the same logical value hashes identically
    regardless of whether it comes from JSON export or Excel cell read.
    """
    if val is None or str(val).strip() == "":
        return ""
    s = str(val).strip().upper()
    # Excel renders integer-like floats as "1.0" — normalize to "1"
    if s.endswith(".0"):
        s = s[:-2]
    return s


def compute_row_hash(
    person_id: UUID,
    rotation1: str | None,
    rotation2: str | None,
    days: list[str | None],
) -> str:
    """
    Compute MD5 hash of row content for change detection.

    Used to skip unchanged rows during import. Uses normalize_for_hash()
    to ensure symmetric hashing between export (JSON strings) and import
    (Excel cell values subject to type coercion).
    """
    nr1 = normalize_for_hash(rotation1)
    nr2 = normalize_for_hash(rotation2)
    nd = "|".join(normalize_for_hash(d) for d in days)
    data = f"{person_id}|{nr1}|{nr2}|{nd}"
    return hashlib.md5(data.encode()).hexdigest()  # nosec B324 — not for security
