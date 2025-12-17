"""Role-based view schemas."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class StaffRole(str, Enum):
    ADMIN = "admin"
    COORDINATOR = "coordinator"
    FACULTY = "faculty"
    CLINICAL_STAFF = "clinical_staff"  # rn, lpn, msa
    RESIDENT = "resident"

class ViewPermissions(BaseModel):
    can_view_all_schedules: bool = False
    can_view_own_schedule: bool = True
    can_view_manifest: bool = True
    can_view_call_roster: bool = True
    can_view_academic_blocks: bool = False
    can_view_compliance: bool = False
    can_view_conflicts: bool = False
    can_manage_swaps: bool = False

class RoleViewConfig(BaseModel):
    role: StaffRole
    permissions: ViewPermissions
