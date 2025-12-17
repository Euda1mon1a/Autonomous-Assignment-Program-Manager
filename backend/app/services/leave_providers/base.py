"""Base classes for leave providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass
class LeaveRecord:
    faculty_name: str
    faculty_id: Optional[str]
    start_date: date
    end_date: date
    leave_type: str
    description: Optional[str] = None
    is_blocking: bool = True


class LeaveProvider(ABC):
    @abstractmethod
    def get_conflicts(self, faculty_name: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[LeaveRecord]:
        pass

    @abstractmethod
    def sync(self) -> int:
        pass

    @abstractmethod
    def get_all_leave(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[LeaveRecord]:
        pass
