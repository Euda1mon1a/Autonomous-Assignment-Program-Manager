"""CSV-based leave provider."""

import csv
from datetime import date, datetime
from pathlib import Path

from app.core.file_security import FileSecurityError, validate_file_path
from app.services.leave_providers.base import LeaveProvider, LeaveRecord

# Default allowed directory for CSV files
# Can be configured via environment or application settings
ALLOWED_CSV_DIR = Path("data/csv_files")


class CSVLeaveProvider(LeaveProvider):
    """Leave provider that reads from CSV files."""

    def __init__(self, file_path: Path, allowed_base_dir: Path | None = None) -> None:
        """
        Initialize CSV leave provider with path validation.

        Args:
            file_path: Path to the CSV file containing leave data
            allowed_base_dir: Optional base directory to validate against.
                             Defaults to ALLOWED_CSV_DIR constant.

        Raises:
            FileSecurityError: If file_path is outside the allowed directory
        """
        # Use provided base directory or default
        base_dir = allowed_base_dir or ALLOWED_CSV_DIR

        # Ensure the allowed base directory exists
        base_dir.mkdir(parents=True, exist_ok=True)

        # Validate that file_path is within the allowed directory
        try:
            validated_path = validate_file_path(file_path, base_dir)
            self.file_path = validated_path
        except FileSecurityError as exc:
            # If validation fails, raise with more context
            raise FileSecurityError(
                f"CSV file path '{file_path}' must be within allowed directory '{base_dir}'"
            ) from exc

        self._records: list[LeaveRecord] = []

    def get_conflicts(
        self,
        faculty_name: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[LeaveRecord]:
        records = self.get_all_leave(start_date, end_date)
        if faculty_name:
            records = [r for r in records if r.faculty_name == faculty_name]
        return [r for r in records if r.is_blocking]

    def sync(self) -> int:
        self._records = self._load_csv()
        return len(self._records)

    def get_all_leave(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> list[LeaveRecord]:
        if not self._records:
            self._records = self._load_csv()
        records = self._records
        if start_date:
            records = [r for r in records if r.end_date >= start_date]
        if end_date:
            records = [r for r in records if r.start_date <= end_date]
        return records

    def _load_csv(self) -> list[LeaveRecord]:
        if not self.file_path.exists():
            return []
        records = []
        with open(self.file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(
                    LeaveRecord(
                        faculty_name=row["faculty_name"],
                        faculty_id=row.get("faculty_id"),
                        start_date=datetime.strptime(
                            row["start_date"], "%Y-%m-%d"
                        ).date(),
                        end_date=datetime.strptime(row["end_date"], "%Y-%m-%d").date(),
                        leave_type=row["leave_type"],
                        description=row.get("description"),
                        is_blocking=row.get("is_blocking", "true").lower() == "true",
                    )
                )
        return records
