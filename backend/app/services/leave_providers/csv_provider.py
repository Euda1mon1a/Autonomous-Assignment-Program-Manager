"""CSV-based leave provider."""
import csv
from datetime import date, datetime
from pathlib import Path

from app.services.leave_providers.base import LeaveProvider, LeaveRecord


class CSVLeaveProvider(LeaveProvider):
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._records: list[LeaveRecord] = []

    def get_conflicts(self, faculty_name: str | None = None, start_date: date | None = None, end_date: date | None = None) -> list[LeaveRecord]:
        records = self.get_all_leave(start_date, end_date)
        if faculty_name:
            records = [r for r in records if r.faculty_name == faculty_name]
        return [r for r in records if r.is_blocking]

    def sync(self) -> int:
        self._records = self._load_csv()
        return len(self._records)

    def get_all_leave(self, start_date: date | None = None, end_date: date | None = None) -> list[LeaveRecord]:
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
        with open(self.file_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(LeaveRecord(
                    faculty_name=row['faculty_name'],
                    faculty_id=row.get('faculty_id'),
                    start_date=datetime.strptime(row['start_date'], '%Y-%m-%d').date(),
                    end_date=datetime.strptime(row['end_date'], '%Y-%m-%d').date(),
                    leave_type=row['leave_type'],
                    description=row.get('description'),
                    is_blocking=row.get('is_blocking', 'true').lower() == 'true',
                ))
        return records
