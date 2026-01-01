"""Role filter response schemas."""

from pydantic import BaseModel


class PermissionsResponse(BaseModel):
    """Response for user permissions and accessible resources."""

    user_id: str
    username: str
    role: str
    accessible_resources: list[str]
    role_description: str


class DashboardResponse(BaseModel):
    """Response for role-filtered dashboard data."""

    message: str
    data: dict


class SchedulesResponse(BaseModel):
    """Response for all schedules (admin/coordinator only)."""

    message: str
    count: int
    schedules: list[dict]


class MyScheduleResponse(BaseModel):
    """Response for user's personal schedule."""

    message: str
    user_id: str
    schedules: list[dict]


class ManifestResponse(BaseModel):
    """Response for daily manifest."""

    message: str
    date: str
    locations: list[dict]


class ComplianceResponse(BaseModel):
    """Response for compliance report."""

    message: str
    data: dict


class CreateUserResponse(BaseModel):
    """Response for user creation."""

    message: str
    user: dict


class RolesResponse(BaseModel):
    """Response for all available roles."""

    message: str
    roles: dict[str, str]


class AccessCheckResponse(BaseModel):
    """Response for access check."""

    user_role: str
    endpoint_category: str
    can_access: bool
    message: str
