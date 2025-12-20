"""Factory for creating leave providers."""
from pathlib import Path

from sqlalchemy.orm import Session

from app.services.leave_providers.base import LeaveProvider
from app.services.leave_providers.csv_provider import CSVLeaveProvider
from app.services.leave_providers.database import DatabaseLeaveProvider


class LeaveProviderFactory:
    """Factory for creating leave data providers."""

    @staticmethod
    def create(
        provider_type: str,
        db: Session | None = None,
        file_path: Path | None = None,
    ) -> LeaveProvider:
        """Create a leave provider of the specified type."""
        if provider_type == "database":
            if db is None:
                raise ValueError("Database session required for database provider")
            return DatabaseLeaveProvider(db)
        elif provider_type == "csv":
            if file_path is None:
                raise ValueError("File path required for CSV provider")
            return CSVLeaveProvider(file_path)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
