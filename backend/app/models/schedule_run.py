"""Schedule run model - audit trail for generated schedules."""
import uuid
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String

from app.db.base import Base
from app.db.types import GUID, JSONType


class ScheduleRun(Base):
    """
    Represents a schedule generation run.

    Used for:
    - Audit trail (who generated what, when)
    - Performance tracking (runtime, success rate)
    - Configuration snapshot (settings used)

    Version history is tracked via SQLAlchemy-Continuum.
    Access history: schedule_run.versions
    """
    __tablename__ = "schedule_runs"
    __versioned__ = {}  # Enable audit trail - tracks all changes with who/what/when

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    algorithm = Column(String(50), nullable=False)  # 'greedy', 'min_conflicts', 'cp_sat'

    # Results
    status = Column(String(50), nullable=False)  # 'success', 'partial', 'failed'
    total_blocks_assigned = Column(Integer)
    acgme_violations = Column(Integer, default=0)
    acgme_override_count = Column(Integer, default=0)  # Number of acknowledged overrides
    runtime_seconds = Column(Numeric(10, 2))

    # Configuration snapshot
    config_json = Column(JSONType())

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ScheduleRun(status='{self.status}', blocks={self.total_blocks_assigned})>"

    @property
    def is_successful(self) -> bool:
        """Check if the run was successful."""
        return self.status == "success"

    @property
    def has_violations(self) -> bool:
        """Check if the run has ACGME violations."""
        return self.acgme_violations is not None and self.acgme_violations > 0
