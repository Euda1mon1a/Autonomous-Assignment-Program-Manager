"""
ACGME Validation Validators Module.

Provides specialized validators for different compliance domains:
- Work Hour Validator: Duty hour limits, shift durations, moonlighting
- Supervision Validator: Faculty-to-resident ratios by PGY level
- Call Validator: Call scheduling, equity, frequency limits
- Leave Validator: Absence blocking, leave policies
- Rotation Validator: Rotation requirements, sequence, volume

All validators follow a consistent pattern:
1. validate_*() methods return (violations, warnings) tuples
2. violations: List of critical/high-severity issues
3. warnings: List of medium/low-severity alerts
4. Each violation/warning includes specific context for reporting

Example usage:
```python
from app.scheduling.validators import WorkHourValidator, SupervisionValidator

# Work hour validation
wh_validator = WorkHourValidator()
violations, warnings = wh_validator.validate_80_hour_rolling_average(
    person_id=resident_id,
    hours_by_date=hours_dict,
    moonlighting_hours=moonlight_dict
)

# Supervision validation
sup_validator = SupervisionValidator()
violation = sup_validator.validate_block_supervision(
    block_id=block_id,
    block_date=date(2025, 12, 30),
    pgy1_residents=[...],
    other_residents=[...],
    faculty_assigned=[...]
)
```
"""

from app.scheduling.validators.call_validator import CallValidator
from app.scheduling.validators.leave_validator import LeaveValidator
from app.scheduling.validators.rotation_validator import RotationValidator
from app.scheduling.validators.supervision_validator import SupervisionValidator
from app.scheduling.validators.work_hour_validator import WorkHourValidator

__all__ = [
    "WorkHourValidator",
    "SupervisionValidator",
    "CallValidator",
    "LeaveValidator",
    "RotationValidator",
]

__version__ = "1.0.0"
