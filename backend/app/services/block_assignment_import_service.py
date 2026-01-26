"""
Block Assignment Import Service.

Handles:
- CSV/Excel parsing for block assignments
- Fuzzy matching for rotations and residents
- Preview generation with match status
- Import execution with duplicate handling
- PERSEC-compliant logging (no PII)
"""

import csv
import io
import re
import uuid
from collections import Counter
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.activity import Activity, ActivityCategory
from app.models.block_assignment import BlockAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.utils.activity_naming import activity_code_from_name, activity_display_abbrev
from app.schemas.block_assignment_import import (
    BlockAssignmentImportRequest,
    BlockAssignmentImportResult,
    BlockAssignmentPreviewItem,
    BlockAssignmentPreviewResponse,
    BlockAssignmentUploadRequest,
    DuplicateAction,
    ImportFormat,
    MatchStatus,
    UnknownRotationItem,
)

logger = get_logger(__name__)


# Combined rotation mappings: (primary, secondary) -> combined template
# Used when xlsx has two rotations that map to a single combined template
# Includes mirror rotations where both orderings map to the same template
# Keys use both full names AND DB abbreviations for flexibility
COMBINED_ROTATION_MAPPINGS: dict[tuple[str, str], str] = {
    # Night Float + Endocrinology (full names and abbreviations)
    ("NIGHT FLOAT", "ENDOCRINOLOGY"): "NF-ENDO",
    ("ENDOCRINOLOGY", "NIGHT FLOAT"): "NF-ENDO",
    ("NF-PM", "ENDO"): "NF-ENDO",
    ("ENDO", "NF-PM"): "NF-ENDO",
    ("NF", "ENDO"): "NF-ENDO",
    ("ENDO", "NF"): "NF-ENDO",
    ("NF", "ENDOCRINOLOGY"): "NF-ENDO",
    ("ENDOCRINOLOGY", "NF"): "NF-ENDO",
    # Night Float + Cardiology (both directions)
    ("NIGHT FLOAT", "CARDIOLOGY"): "NF+",
    ("CARDIOLOGY", "NIGHT FLOAT"): "C+N",
    ("NF-PM", "CARDIO"): "NF+",
    ("CARDIO", "NF-PM"): "C+N",
    ("NF", "CARDIOLOGY"): "NF+",
    ("CARDIOLOGY", "NF"): "C+N",
    # Night Float + Dermatology (both directions)
    ("NIGHT FLOAT", "DERMATOLOGY"): "NF-DERM",
    ("DERMATOLOGY", "NIGHT FLOAT"): "D+N",
    ("NF-PM", "DERM"): "NF-DERM",
    ("DERM", "NF-PM"): "D+N",
    ("NF", "DERMATOLOGY"): "NF-DERM",
    ("DERMATOLOGY", "NF"): "D+N",
    # Night Float + Medical Selective
    ("NIGHT FLOAT", "MEDICAL SELECTIVE"): "NF-MED",
    ("MEDICAL SELECTIVE", "NIGHT FLOAT"): "NF-MED",
    ("NF-PM", "MED SEL"): "NF-MED",
    ("MED SEL", "NF-PM"): "NF-MED",
    ("NF", "MED SEL"): "NF-MED",
    ("MED SEL", "NF"): "NF-MED",
    # Night Float + NICU
    ("NIGHT FLOAT", "NICU"): "NF-NICU",
    ("NICU", "NIGHT FLOAT"): "NIC",
    ("NF-PM", "NICU"): "NF-NICU",
    ("NICU", "NF-PM"): "NIC",
    ("NF", "NICU"): "NF-NICU",
    ("NICU", "NF"): "NIC",
    # Neurology + Night Float (both directions)
    ("NEUROLOGY", "NIGHT FLOAT"): "NEURO-NF",
    ("NIGHT FLOAT", "NEUROLOGY"): "NEURO-NF",
    ("NEURO", "NF-PM"): "NEURO-NF",
    ("NF-PM", "NEURO"): "NEURO-NF",
    ("NEURO", "NF"): "NEURO-NF",
    ("NF", "NEURO"): "NEURO-NF",
    ("NEURO", "NIGHT FLOAT"): "NEURO-NF",
    ("NIGHT FLOAT", "NEURO"): "NEURO-NF",
    # Pediatrics Ward <-> Pediatrics Night Float (full names and abbreviations)
    ("PEDIATRICS WARD", "PEDIATRICS NIGHT FLOAT"): "PEDS-W",
    ("PEDIATRICS NIGHT FLOAT", "PEDIATRICS WARD"): "PNF",
    ("PEDS-W", "PNF"): "PEDS-W",
    ("PNF", "PEDS-W"): "PNF",
    ("PEDS WARD", "PEDS NF"): "PEDS-W",
    ("PEDS NF", "PEDS WARD"): "PNF",
}

# Single-rotation synonym mappings (xlsx/CSV inputs -> canonical abbreviations)
ROTATION_SYNONYMS: dict[str, str] = {
    # Surgical Experience
    "SURG-EXP": "SURG",
    "SURG EXP": "SURG",
    "SURGICAL EXPERIENCE": "SURG",
    # GYN Clinic
    "GYN-CLIN": "GYN",
    "GYN CLINIC": "GYN",
    "GYNECOLOGY CLINIC": "GYN",
    # Kapiolani L&D
    "KAPI-LD": "KAPI-LD-PGY1",
    "KAPI L&D": "KAPI-LD-PGY1",
    "KAPIOLANI L AND D": "KAPI-LD-PGY1",
    "KAPIOLANI L&D": "KAPI-LD-PGY1",
    # Procedures
    "PR-AM": "PROC-AM",
    "PROC": "PROC-AM",
    "PROCEDURES": "PROC-AM",
    # Internal Medicine
    "IM-INT": "IM",
    "INTERNAL MEDICINE": "IM",
}


class BlockAssignmentImportService:
    """
    Service for importing block assignments from CSV/Excel.

    Key features:
    - Fuzzy matching for rotation templates
    - Fuzzy matching for resident names
    - Preview mode with match status
    - Duplicate detection and handling
    - PERSEC compliance (no PII in logs)
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._rotation_cache: dict[str, tuple[uuid.UUID, str]] = {}
        self._resident_cache: dict[str, tuple[uuid.UUID, str]] = {}
        self._resident_pgy_cache: dict[uuid.UUID, int | None] = {}
        self._preview_cache: dict[str, list[dict[str, Any]]] = {}

    async def load_caches(self) -> None:
        """Pre-load rotation templates and residents for fast lookup."""
        # Load rotation templates
        result = await self.session.execute(
            select(RotationTemplate).where(RotationTemplate.is_archived == False)  # noqa: E712
        )
        templates = result.scalars().all()

        for t in templates:
            # Index by multiple keys for flexible matching
            keys_to_add = []
            if t.abbreviation:
                keys_to_add.append(t.abbreviation.upper())
            if t.display_abbreviation:
                keys_to_add.append(t.display_abbreviation.upper())
            if t.name:
                keys_to_add.append(t.name.upper())

            for key in keys_to_add:
                if key not in self._rotation_cache:
                    self._rotation_cache[key] = (t.id, t.name)

        logger.info(f"Loaded {len(templates)} rotation templates into cache")

        # Load residents
        result = await self.session.execute(
            select(Person).where(Person.type == "resident")
        )
        residents = result.scalars().all()

        for r in residents:
            # Index by each name part (case-insensitive)
            name_parts = r.name.replace(",", " ").split()
            for part in name_parts:
                # Skip common prefixes
                if part.lower() in ("dr", "dr.", "md", "do"):
                    continue
                key = part.upper()
                if key not in self._resident_cache:
                    self._resident_cache[key] = (r.id, r.name)
            self._resident_pgy_cache[r.id] = r.pgy_level

        logger.info(f"Loaded {len(residents)} residents into cache")

    def _anonymize_name(self, name: str) -> str:
        """
        Anonymize a name for PERSEC compliance.

        Args:
            name: Full name (e.g., "Smith, John")

        Returns:
            Anonymized name (e.g., "S*****, J***")
        """
        if not name:
            return "****"

        parts = name.split(",")
        if len(parts) == 2:
            last = parts[0].strip()
            first = parts[1].strip()
            last_anon = last[0] + "*" * max(0, len(last) - 1) if last else "***"
            first_anon = first[0] + "*" * max(0, len(first) - 1) if first else "***"
            return f"{last_anon}, {first_anon}"

        # Single name or other format
        parts = name.split()
        anon_parts = []
        for part in parts:
            if part:
                anon_parts.append(part[0] + "*" * max(0, len(part) - 1))
        return " ".join(anon_parts) if anon_parts else "****"

    def _match_rotation(
        self, abbrev: str
    ) -> tuple[uuid.UUID | None, str | None, float]:
        """
        Match rotation abbreviation to template.

        Args:
            abbrev: Rotation abbreviation from source

        Returns:
            Tuple of (rotation_id, rotation_name, confidence)
        """
        key = abbrev.upper().strip()

        # Direct match
        if key in self._rotation_cache:
            rot_id, rot_name = self._rotation_cache[key]
            return rot_id, rot_name, 1.0

        # Try common variations
        variations = [
            key.replace(" ", "-"),
            key.replace("-", " "),
            key.replace("/", "-"),
            key.replace("_", "-"),
            key.replace("-", ""),
        ]
        for var in variations:
            if var in self._rotation_cache:
                rot_id, rot_name = self._rotation_cache[var]
                return rot_id, rot_name, 0.9

        return None, None, 0.0

    def _normalize_rotation_input(
        self, rotation_input: str, resident_id: uuid.UUID | None
    ) -> str:
        """
        Normalize rotation inputs to canonical abbreviations.

        Handles:
        - Synonym mapping (SURG-EXP -> SURG, IM-INT -> IM)
        - FMIT rotations resolved by PGY level when possible
        """
        key = rotation_input.upper().strip()
        key = ROTATION_SYNONYMS.get(key, key)

        # FMIT is PGY-specific; try to resolve from input or resident PGY level
        if key.startswith("FMIT"):
            pgy = None
            match = re.search(r"([123])", key)
            if match:
                pgy = int(match.group(1))
            if pgy is None and resident_id:
                pgy = self._resident_pgy_cache.get(resident_id)
            if pgy in (1, 2, 3):
                return f"FMIT-PGY{pgy}"
            # Fallback to a deterministic template to avoid unknown-rotation noise
            return "FMIT-PGY1"

        return key

    def _match_combined_rotation(
        self, primary: str, secondary: str
    ) -> tuple[uuid.UUID | None, str | None, float]:
        """
        Match a primary + secondary rotation pair to a combined template.

        Args:
            primary: Primary rotation from xlsx column A
            secondary: Secondary rotation from xlsx column B

        Returns:
            Tuple of (rotation_id, rotation_name, confidence)
        """
        if not primary or not secondary:
            return None, None, 0.0

        key = (primary.upper().strip(), secondary.upper().strip())

        # Look up in combined mappings
        if key in COMBINED_ROTATION_MAPPINGS:
            combined_abbrev = COMBINED_ROTATION_MAPPINGS[key]
            # Look up the combined template
            if combined_abbrev.upper() in self._rotation_cache:
                rot_id, rot_name = self._rotation_cache[combined_abbrev.upper()]
                logger.debug(
                    f"Combined rotation match: {primary} + {secondary} -> {combined_abbrev}"
                )
                return rot_id, rot_name, 1.0

        # Try variations of the keys
        variations = [
            (primary.upper().replace(" ", "-"), secondary.upper().replace(" ", "-")),
            (primary.upper().replace("-", " "), secondary.upper().replace("-", " ")),
        ]
        for var_key in variations:
            if var_key in COMBINED_ROTATION_MAPPINGS:
                combined_abbrev = COMBINED_ROTATION_MAPPINGS[var_key]
                if combined_abbrev.upper() in self._rotation_cache:
                    rot_id, rot_name = self._rotation_cache[combined_abbrev.upper()]
                    return rot_id, rot_name, 0.9

        logger.warning(f"No combined template found for: {primary} + {secondary}")
        return None, None, 0.0

    def _match_resident(self, name: str) -> tuple[uuid.UUID | None, str | None, float]:
        """
        Match resident name to person.

        Args:
            name: Resident name from source

        Returns:
            Tuple of (resident_id, full_name, confidence)
        """
        # Clean and split name
        clean_name = name.strip().replace(",", " ")
        parts = clean_name.split()

        # Try each part (last name usually most unique)
        for part in parts:
            key = part.upper()
            if key in self._resident_cache:
                res_id, res_name = self._resident_cache[key]
                return res_id, res_name, 1.0

        return None, None, 0.0

    async def _check_duplicate(
        self, block_number: int, academic_year: int, resident_id: uuid.UUID
    ) -> tuple[bool, uuid.UUID | None]:
        """
        Check if assignment already exists.

        Returns:
            Tuple of (is_duplicate, existing_assignment_id)
        """
        result = await self.session.execute(
            select(BlockAssignment).where(
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == academic_year,
                BlockAssignment.resident_id == resident_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return True, existing.id
        return False, None

    def _calculate_academic_year(self) -> int:
        """
        Calculate current academic year based on date.

        Academic year starts July 1:
        - July-December = current calendar year
        - January-June = previous calendar year
        """
        now = datetime.now()
        if now.month >= 7:
            return now.year
        else:
            return now.year - 1

    def _parse_csv_content(self, content: str) -> list[dict[str, Any]]:
        """
        Parse CSV content into row dictionaries.

        Handles:
        - Comment lines (starting with #)
        - Multiple header variations
        - Whitespace normalization
        """
        rows = []

        # Filter out comment lines
        lines = [
            line
            for line in content.strip().split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        if not lines:
            return rows

        # Parse CSV
        reader = csv.DictReader(io.StringIO("\n".join(lines)))

        if reader.fieldnames:
            # Normalize header names
            reader.fieldnames = [h.lower().strip() for h in reader.fieldnames]

        for row_num, row in enumerate(reader, start=2):  # Header is row 1
            rows.append(
                {
                    "row_number": row_num,
                    "block_number": row.get("block_number")
                    or row.get("block")
                    or row.get("blk"),
                    "rotation_abbrev": row.get("rotation_abbrev")
                    or row.get("rotation_name")
                    or row.get("rotation")
                    or row.get("rot"),
                    "resident_name": row.get("resident_name")
                    or row.get("resident")
                    or row.get("name"),
                }
            )

        return rows

    async def preview_import(
        self, request: BlockAssignmentUploadRequest
    ) -> BlockAssignmentPreviewResponse:
        """
        Generate import preview with match status for each row.

        Args:
            request: Upload request with CSV content

        Returns:
            Preview response with items and summary
        """
        await self.load_caches()

        # Generate preview ID
        preview_id = str(uuid.uuid4())

        # Calculate academic year
        academic_year = request.academic_year or self._calculate_academic_year()

        # Parse content
        rows = self._parse_csv_content(request.content)

        # Track unknown rotations
        unknown_rotation_counts: Counter[str] = Counter()

        # Process each row
        items: list[BlockAssignmentPreviewItem] = []
        warnings: list[str] = []

        for row in rows:
            row_num = row["row_number"]
            errors: list[str] = []
            row_warnings: list[str] = []

            # Parse block number
            try:
                block_number = int(row["block_number"])
                if not (0 <= block_number <= 13):
                    errors.append(f"Block number {block_number} out of range (0-13)")
            except (TypeError, ValueError):
                block_number = 0
                errors.append("Invalid block number")

            rotation_input = str(row["rotation_abbrev"] or "").strip()
            resident_input = str(row["resident_name"] or "").strip()

            # Match resident
            resident_id, resident_name, resident_conf = self._match_resident(
                resident_input
            )

            # Match rotation (normalize with resident context for FMIT)
            normalized_rotation = self._normalize_rotation_input(
                rotation_input, resident_id
            )
            rotation_id, rotation_name, rotation_conf = self._match_rotation(
                normalized_rotation
            )
            if not rotation_id:
                unknown_rotation_counts[rotation_input.upper()] += 1

            # Check for duplicate
            is_duplicate = False
            existing_assignment_id = None
            if rotation_id and resident_id:
                is_duplicate, existing_assignment_id = await self._check_duplicate(
                    block_number, academic_year, resident_id
                )

            # Determine match status
            if errors:
                match_status = MatchStatus.INVALID
            elif not rotation_id:
                match_status = MatchStatus.UNKNOWN_ROTATION
            elif not resident_id:
                match_status = MatchStatus.UNKNOWN_RESIDENT
            elif is_duplicate:
                match_status = MatchStatus.DUPLICATE
            else:
                match_status = MatchStatus.MATCHED

            # Add low confidence warnings
            if rotation_conf > 0 and rotation_conf < 1.0:
                row_warnings.append(
                    f"Rotation matched with {rotation_conf * 100:.0f}% confidence"
                )
            if resident_conf > 0 and resident_conf < 1.0:
                row_warnings.append(
                    f"Resident matched with {resident_conf * 100:.0f}% confidence"
                )

            items.append(
                BlockAssignmentPreviewItem(
                    row_number=row_num,
                    block_number=block_number,
                    rotation_input=rotation_input,
                    resident_display=self._anonymize_name(
                        resident_name or resident_input
                    ),
                    match_status=match_status,
                    matched_rotation_id=rotation_id,
                    matched_rotation_name=rotation_name,
                    rotation_confidence=rotation_conf,
                    matched_resident_id=resident_id,
                    resident_confidence=resident_conf,
                    is_duplicate=is_duplicate,
                    existing_assignment_id=existing_assignment_id,
                    duplicate_action=DuplicateAction.SKIP,
                    errors=errors,
                    warnings=row_warnings,
                )
            )

        # Build unknown rotations list
        unknown_rotations = [
            UnknownRotationItem(
                abbreviation=abbrev,
                occurrences=count,
                suggested_name=self._suggest_rotation_name(abbrev),
            )
            for abbrev, count in unknown_rotation_counts.most_common()
        ]

        # Calculate summary statistics
        matched_count = sum(1 for i in items if i.match_status == MatchStatus.MATCHED)
        unknown_rotation_count = sum(
            1 for i in items if i.match_status == MatchStatus.UNKNOWN_ROTATION
        )
        unknown_resident_count = sum(
            1 for i in items if i.match_status == MatchStatus.UNKNOWN_RESIDENT
        )
        duplicate_count = sum(
            1 for i in items if i.match_status == MatchStatus.DUPLICATE
        )
        invalid_count = sum(1 for i in items if i.match_status == MatchStatus.INVALID)

        # Cache preview data for import execution
        self._preview_cache[preview_id] = [
            {
                "row_number": item.row_number,
                "block_number": item.block_number,
                "rotation_id": str(item.matched_rotation_id)
                if item.matched_rotation_id
                else None,
                "resident_id": str(item.matched_resident_id)
                if item.matched_resident_id
                else None,
                "match_status": item.match_status.value,
                "is_duplicate": item.is_duplicate,
                "existing_assignment_id": str(item.existing_assignment_id)
                if item.existing_assignment_id
                else None,
            }
            for item in items
        ]

        # Log summary (no PII)
        logger.info(
            f"Preview generated: {len(items)} rows, "
            f"{matched_count} matched, {unknown_rotation_count} unknown rotations, "
            f"{unknown_resident_count} unknown residents, {duplicate_count} duplicates"
        )

        return BlockAssignmentPreviewResponse(
            preview_id=preview_id,
            academic_year=academic_year,
            format_detected=request.format,
            items=items,
            total_rows=len(items),
            matched_count=matched_count,
            unknown_rotation_count=unknown_rotation_count,
            unknown_resident_count=unknown_resident_count,
            duplicate_count=duplicate_count,
            invalid_count=invalid_count,
            unknown_rotations=unknown_rotations,
            warnings=warnings,
        )

    def _suggest_rotation_name(self, abbrev: str) -> str | None:
        """Suggest a full name based on common abbreviation patterns."""
        suggestions = {
            "CARDIO": "Cardiology",
            "DERM": "Dermatology",
            "ELEC": "Elective",
            "EM": "Emergency Medicine",
            "FAC-DEV": "Faculty Development",
            "GERI": "Geriatrics",
            "IM": "Internal Medicine Ward",
            "MSK": "Musculoskeletal",
            "PEDS": "Pediatrics",
            "PROC": "Procedures",
            "PSYCH": "Psychiatry",
        }
        return suggestions.get(abbrev.upper())

    async def execute_import(
        self, request: BlockAssignmentImportRequest
    ) -> BlockAssignmentImportResult:
        """
        Execute the import based on preview.

        Args:
            request: Import request with preview_id and options

        Returns:
            Import result with counts and errors
        """
        started_at = datetime.utcnow()

        # Get cached preview data
        preview_data = self._preview_cache.get(request.preview_id)
        if not preview_data:
            return BlockAssignmentImportResult(
                success=False,
                academic_year=request.academic_year,
                total_rows=0,
                imported_count=0,
                updated_count=0,
                skipped_count=0,
                failed_count=0,
                error_messages=["Preview not found. Please re-upload."],
                started_at=started_at,
                completed_at=datetime.utcnow(),
            )

        imported_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        failed_rows: list[int] = []
        error_messages: list[str] = []

        for row_data in preview_data:
            row_num = row_data["row_number"]
            match_status = row_data["match_status"]

            # Skip invalid rows
            if match_status == MatchStatus.INVALID.value:
                skipped_count += 1
                continue

            # Skip unknown rotations/residents
            if match_status == MatchStatus.UNKNOWN_ROTATION.value:
                skipped_count += 1
                continue

            if match_status == MatchStatus.UNKNOWN_RESIDENT.value:
                skipped_count += 1
                continue

            # Handle duplicates
            if match_status == MatchStatus.DUPLICATE.value:
                # Check row-specific override
                row_action = request.row_overrides.get(row_num, DuplicateAction.SKIP)

                if request.update_duplicates or row_action == DuplicateAction.UPDATE:
                    # Update existing assignment
                    try:
                        existing_id = uuid.UUID(row_data["existing_assignment_id"])
                        result = await self.session.execute(
                            select(BlockAssignment).where(
                                BlockAssignment.id == existing_id
                            )
                        )
                        existing = result.scalar_one_or_none()
                        if existing:
                            existing.rotation_template_id = uuid.UUID(
                                row_data["rotation_id"]
                            )
                            # Update secondary rotation (or clear if not present)
                            if row_data.get("secondary_rotation_id"):
                                existing.secondary_rotation_template_id = uuid.UUID(
                                    row_data["secondary_rotation_id"]
                                )
                            else:
                                existing.secondary_rotation_template_id = None
                            existing.assignment_reason = "manual"
                            existing.created_by = "gui_import"
                            existing.updated_at = datetime.utcnow()
                            updated_count += 1
                    except Exception as e:
                        logger.error(f"Row {row_num}: Update failed - {e}")
                        failed_count += 1
                        failed_rows.append(row_num)
                        error_messages.append(f"Row {row_num}: Update failed")
                else:
                    skipped_count += 1
                continue

            # Create new assignment
            try:
                # Parse secondary rotation ID if present
                secondary_rot_id = None
                if row_data.get("secondary_rotation_id"):
                    secondary_rot_id = uuid.UUID(row_data["secondary_rotation_id"])

                assignment = BlockAssignment(
                    block_number=row_data["block_number"],
                    academic_year=request.academic_year,
                    resident_id=uuid.UUID(row_data["resident_id"]),
                    rotation_template_id=uuid.UUID(row_data["rotation_id"]),
                    secondary_rotation_template_id=secondary_rot_id,
                    assignment_reason="manual",
                    created_by="gui_import",
                )
                self.session.add(assignment)
                imported_count += 1
            except Exception as e:
                logger.error(f"Row {row_num}: Import failed - {e}")
                failed_count += 1
                failed_rows.append(row_num)
                error_messages.append(f"Row {row_num}: Import failed")

        # Commit transaction
        try:
            await self.session.commit()
            logger.info(
                f"Import completed: {imported_count} imported, "
                f"{updated_count} updated, {skipped_count} skipped, "
                f"{failed_count} failed"
            )
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Import transaction failed: {e}")
            return BlockAssignmentImportResult(
                success=False,
                academic_year=request.academic_year,
                total_rows=len(preview_data),
                imported_count=0,
                updated_count=0,
                skipped_count=0,
                failed_count=len(preview_data),
                error_messages=["Transaction failed. All changes rolled back."],
                started_at=started_at,
                completed_at=datetime.utcnow(),
            )

        # Clean up preview cache
        del self._preview_cache[request.preview_id]

        return BlockAssignmentImportResult(
            success=failed_count == 0,
            academic_year=request.academic_year,
            total_rows=len(preview_data),
            imported_count=imported_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            failed_rows=failed_rows,
            error_messages=error_messages,
            started_at=started_at,
            completed_at=datetime.utcnow(),
        )

    async def create_quick_template(
        self, abbreviation: str, name: str, activity_type: str, leave_eligible: bool
    ) -> RotationTemplate:
        """
        Create a new rotation template quickly during import.

        Args:
            abbreviation: Short abbreviation
            name: Full name
            activity_type: Activity type
            leave_eligible: Whether rotation allows leave

        Returns:
            Created RotationTemplate
        """
        template = RotationTemplate(
            abbreviation=abbreviation.upper(),
            display_abbreviation=abbreviation.upper()[:4],
            name=name,
            activity_type=activity_type,
            leave_eligible=leave_eligible,
            is_archived=False,
        )
        self.session.add(template)
        await self.session.flush()
        await self._ensure_activity_for_template(template)
        await self.session.commit()
        await self.session.refresh(template)

        # Update cache
        self._rotation_cache[abbreviation.upper()] = (template.id, template.name)

        logger.info(f"Created rotation template: {abbreviation}")

        return template

    async def _ensure_activity_for_template(self, template: RotationTemplate) -> None:
        """Create a specialty activity for outpatient/clinic templates if missing."""
        if (template.activity_type or "").lower() not in ("clinic", "outpatient"):
            return

        code = activity_code_from_name(template.name)
        display_abbrev = activity_display_abbrev(
            template.name,
            template.display_abbreviation,
            template.abbreviation,
        )

        existing = await self.session.execute(
            select(Activity).where(Activity.name == template.name)
        )
        if existing.scalars().first():
            return

        existing = await self.session.execute(
            select(Activity).where(Activity.code.ilike(code))
        )
        if existing.scalars().first():
            return

        activity = Activity(
            name=template.name,
            code=code,
            display_abbreviation=display_abbrev,
            activity_category=ActivityCategory.CLINICAL.value,
            font_color=template.font_color,
            background_color=template.background_color,
            requires_supervision=True,
            is_protected=False,
            counts_toward_clinical_hours=True,
            provides_supervision=False,
            counts_toward_physical_capacity=True,
            display_order=0,
        )
        self.session.add(activity)
        await self.session.flush()

    async def preview_block_sheet_import(
        self, file_bytes: bytes, academic_year: int | None = None
    ) -> BlockAssignmentPreviewResponse:
        """
        Generate import preview from TRIPLER-format block schedule xlsx.

        Processes xlsx directly to preserve secondary rotation (column B)
        for mid-block transitions. Does NOT convert to CSV.

        Args:
            file_bytes: Excel file as bytes
            academic_year: Optional academic year override

        Returns:
            Preview response with items and summary
        """
        from app.services.block_schedule_parser import BlockScheduleParser

        # Parse the xlsx file
        parser = BlockScheduleParser()
        assignments = parser.parse_bytes(file_bytes)

        if not assignments:
            return BlockAssignmentPreviewResponse(
                preview_id="",
                format_detected=ImportFormat.XLSX,
                items=[],
                total_rows=0,
                matched_count=0,
                unknown_rotation_count=0,
                unknown_resident_count=0,
                duplicate_count=0,
                invalid_count=0,
                unknown_rotations=[],
                academic_year=academic_year or self._calculate_academic_year(),
                warnings=["No resident assignments found in file"],
            )

        # Load caches for matching
        await self.load_caches()

        preview_id = str(uuid.uuid4())
        academic_year = academic_year or self._calculate_academic_year()

        items: list[BlockAssignmentPreviewItem] = []
        unknown_rotation_counts: Counter[str] = Counter()
        warnings: list[str] = []

        for idx, a in enumerate(assignments, start=1):
            errors: list[str] = []
            row_warnings: list[str] = []

            # If secondary rotation is present, try combined rotation match first
            rotation_id, rotation_name, rotation_conf = None, None, 0.0
            secondary_id, secondary_name, secondary_conf = None, None, 0.0
            used_combined = False

            if a.secondary_rotation:
                # Try to match to a combined template (e.g., "Night Float" + "Endo" -> "NF-ENDO")
                combined_id, combined_name, combined_conf = (
                    self._match_combined_rotation(
                        a.rotation_template, a.secondary_rotation
                    )
                )
                if combined_id:
                    # Use the combined template as the primary rotation
                    rotation_id = combined_id
                    rotation_name = combined_name
                    rotation_conf = combined_conf
                    used_combined = True
                    row_warnings.append(
                        f"Combined: {a.rotation_template} + {a.secondary_rotation} -> {combined_name}"
                    )

            # Fall back to matching primary rotation separately
            if not rotation_id:
                rotation_id, rotation_name, rotation_conf = self._match_rotation(
                    a.rotation_template
                )
                if not rotation_id and a.rotation_template:
                    unknown_rotation_counts[a.rotation_template.upper()] += 1

            # Match secondary rotation separately (if not using combined)
            if a.secondary_rotation and not used_combined:
                secondary_id, secondary_name, secondary_conf = self._match_rotation(
                    a.secondary_rotation
                )
                if not secondary_id:
                    unknown_rotation_counts[a.secondary_rotation.upper()] += 1
                    row_warnings.append(
                        f"Secondary rotation '{a.secondary_rotation}' not found"
                    )

            # Match resident
            resident_id, resident_name, resident_conf = self._match_resident(
                a.person_name
            )

            # Check for duplicate
            is_duplicate = False
            existing_assignment_id = None
            if rotation_id and resident_id:
                is_duplicate, existing_assignment_id = await self._check_duplicate(
                    a.block_number, academic_year, resident_id
                )

            # Determine match status
            if not rotation_id:
                match_status = MatchStatus.UNKNOWN_ROTATION
            elif not resident_id:
                match_status = MatchStatus.UNKNOWN_RESIDENT
            elif is_duplicate:
                match_status = MatchStatus.DUPLICATE
            else:
                match_status = MatchStatus.MATCHED

            # Add low confidence warnings
            if rotation_conf > 0 and rotation_conf < 1.0:
                row_warnings.append(
                    f"Rotation matched with {rotation_conf * 100:.0f}% confidence"
                )
            if resident_conf > 0 and resident_conf < 1.0:
                row_warnings.append(
                    f"Resident matched with {resident_conf * 100:.0f}% confidence"
                )

            items.append(
                BlockAssignmentPreviewItem(
                    row_number=idx,
                    block_number=a.block_number,
                    rotation_input=a.rotation_template,
                    secondary_rotation_input=a.secondary_rotation,
                    resident_display=self._anonymize_name(
                        resident_name or a.person_name
                    ),
                    match_status=match_status,
                    matched_rotation_id=rotation_id,
                    matched_rotation_name=rotation_name,
                    rotation_confidence=rotation_conf,
                    matched_secondary_rotation_id=secondary_id,
                    matched_secondary_rotation_name=secondary_name,
                    secondary_rotation_confidence=secondary_conf,
                    matched_resident_id=resident_id,
                    resident_confidence=resident_conf,
                    is_duplicate=is_duplicate,
                    existing_assignment_id=existing_assignment_id,
                    duplicate_action=DuplicateAction.SKIP,
                    errors=errors,
                    warnings=row_warnings,
                )
            )

        # Build unknown rotations list
        unknown_rotations = [
            UnknownRotationItem(
                abbreviation=abbrev,
                occurrences=count,
                suggested_name=self._suggest_rotation_name(abbrev),
            )
            for abbrev, count in unknown_rotation_counts.most_common()
        ]

        # Calculate summary statistics
        matched_count = sum(1 for i in items if i.match_status == MatchStatus.MATCHED)
        unknown_rotation_count = sum(
            1 for i in items if i.match_status == MatchStatus.UNKNOWN_ROTATION
        )
        unknown_resident_count = sum(
            1 for i in items if i.match_status == MatchStatus.UNKNOWN_RESIDENT
        )
        duplicate_count = sum(
            1 for i in items if i.match_status == MatchStatus.DUPLICATE
        )
        invalid_count = sum(1 for i in items if i.match_status == MatchStatus.INVALID)

        # Cache preview data for import execution (includes secondary rotation)
        self._preview_cache[preview_id] = [
            {
                "row_number": item.row_number,
                "block_number": item.block_number,
                "rotation_id": str(item.matched_rotation_id)
                if item.matched_rotation_id
                else None,
                "secondary_rotation_id": str(item.matched_secondary_rotation_id)
                if item.matched_secondary_rotation_id
                else None,
                "resident_id": str(item.matched_resident_id)
                if item.matched_resident_id
                else None,
                "match_status": item.match_status.value,
                "is_duplicate": item.is_duplicate,
                "existing_assignment_id": str(item.existing_assignment_id)
                if item.existing_assignment_id
                else None,
            }
            for item in items
        ]

        # Log summary (no PII)
        logger.info(
            f"XLSX preview generated: {len(items)} rows, "
            f"{matched_count} matched, {unknown_rotation_count} unknown rotations, "
            f"{unknown_resident_count} unknown residents, {duplicate_count} duplicates"
        )

        return BlockAssignmentPreviewResponse(
            preview_id=preview_id,
            academic_year=academic_year,
            format_detected=ImportFormat.XLSX,
            items=items,
            total_rows=len(items),
            matched_count=matched_count,
            unknown_rotation_count=unknown_rotation_count,
            unknown_resident_count=unknown_resident_count,
            duplicate_count=duplicate_count,
            invalid_count=invalid_count,
            unknown_rotations=unknown_rotations,
            warnings=warnings,
        )


# Factory function for dependency injection
def get_block_assignment_import_service(
    session: AsyncSession,
) -> BlockAssignmentImportService:
    """Get BlockAssignmentImportService instance."""
    return BlockAssignmentImportService(session)
