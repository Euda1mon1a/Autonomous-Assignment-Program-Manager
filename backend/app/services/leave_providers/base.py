"""Base classes for leave providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class LeaveRecord:
    """Represents a single leave record for a faculty member."""

    faculty_name: str
    faculty_id: str | None
    start_date: date
    end_date: date
    leave_type: str
    description: str | None = None
    is_blocking: bool = True


class LeaveProvider(ABC):
    """Abstract base class for leave data providers."""

    @abstractmethod
    def get_conflicts(
        self,
        faculty_name: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[LeaveRecord]:
        """Get leave records that may conflict with scheduling."""

    @abstractmethod
    def sync(self) -> int:
        """Synchronize leave data from source. Returns count of records."""

    @abstractmethod
    def get_all_leave(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[LeaveRecord]:
        """Get all leave records within date range."""
