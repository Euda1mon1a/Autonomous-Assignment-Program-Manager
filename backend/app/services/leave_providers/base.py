"""Base classes for leave providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class LeaveRecord:
    faculty_name: str
    faculty_id: str | None
    start_date: date
    end_date: date
    leave_type: str
    description: str | None = None
    is_blocking: bool = True


class LeaveProvider(ABC):
    @abstractmethod
    def get_conflicts(self, faculty_name: str | None = None, start_date: date | None = None, end_date: date | None = None) -> list[LeaveRecord]:
        pass

    @abstractmethod
    def sync(self) -> int:
        pass

    @abstractmethod
    def get_all_leave(self, start_date: date | None = None, end_date: date | None = None) -> list[LeaveRecord]:
        pass
