"""Example API routes demonstrating role-based filtering usage.

This module shows how to use RoleFilterService and its dependencies
in FastAPI route handlers.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.role_filter import (
    require_admin,
    require_resource_access,
)
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.role_filter_service import (
    ResourceType,
    RoleFilterService,
    UserRole,
)

router = APIRouter(prefix="/api/example", tags=["Role Filter Examples"])


@router.get("/permissions")
async def get_my_permissions(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Get current user's permissions and accessible resources.

    Returns:
        Dictionary with role information and list of accessible resources
    """
    return {
        "user_id": str(current_user.id),
        "username": current_user.username,
        "role": current_user.role,
        "accessible_resources": RoleFilterService.get_accessible_resources(
            current_user.role
        ),
        "role_description": RoleFilterService.get_role_description(current_user.role),
    }


@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Get dashboard data filtered by user role.

    Different users will see different data based on their role:
    - Admin: Everything
    - Coordinator: Schedules, people, conflicts
    - Faculty: Own schedule, swaps
    - Clinical Staff: Today's manifest, call roster

    Returns:
        Filtered dashboard data
    """
    # Build complete dashboard data
    raw_data = {
        "schedules": [
            {
                "id": 1,
                "person_id": str(current_user.id),
                "date": "2025-01-15",
                "activity": "Clinic",
            },
            {
                "id": 2,
                "person_id": "other-user",
                "date": "2025-01-15",
                "activity": "ICU",
            },
        ],
        "people": [
            {"id": 1, "name": "Dr. Smith", "role": "faculty"},
            {"id": 2, "name": "Dr. Jones", "role": "faculty"},
        ],
        "compliance": {
            "status": "compliant",
            "violations": [],
        },
        "users": [
            {"id": 1, "username": "admin", "role": "admin"},
            {"id": 2, "username": "coordinator1", "role": "coordinator"},
        ],
        "manifest": [
            {"location": "Main Clinic", "staff_count": 5},
            {"location": "ICU", "staff_count": 3},
        ],
        "call_roster": [
            {"name": "Dr. Smith", "phone": "555-1234"},
            {"name": "Dr. Jones", "phone": "555-5678"},
        ],
    }

    # Apply role-based filtering
    filtered_data = RoleFilterService.filter_for_role(
        raw_data, current_user.role, str(current_user.id)
    )

    return {
        "message": f"Dashboard for {current_user.role}",
        "data": filtered_data,
    }


@router.get("/schedules")
async def get_schedules(
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_resource_access(ResourceType.SCHEDULES)),
) -> dict[str, Any]:
    """Get all schedules (requires schedule access permission).

    This endpoint is accessible by:
    - Admin
    - Coordinator

    Blocked for:
    - Faculty (can only see own schedule)
    - Clinical Staff (can only see today's manifest)

    Returns:
        List of all schedules
    """
    schedules = [
        {"id": 1, "person": "Dr. Smith", "date": "2025-01-15"},
        {"id": 2, "person": "Dr. Jones", "date": "2025-01-15"},
    ]

    return {
        "message": "All schedules (admin/coordinator only)",
        "count": len(schedules),
        "schedules": schedules,
    }


@router.get("/my-schedule")
async def get_my_schedule(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Get current user's own schedule.

    Accessible by all authenticated users (faculty, residents, clinical staff can see their own).

    Returns:
        User's personal schedule
    """
    # Simulate fetching user's schedule
    all_schedules = [
        {
            "id": 1,
            "person_id": str(current_user.id),
            "date": "2025-01-15",
            "activity": "Clinic",
        },
        {"id": 2, "person_id": "other-user", "date": "2025-01-15", "activity": "ICU"},
        {
            "id": 3,
            "person_id": str(current_user.id),
            "date": "2025-01-16",
            "activity": "Rounds",
        },
    ]

    # Filter to only user's schedules
    my_schedules = RoleFilterService.filter_schedule_list(
        all_schedules, current_user.role, str(current_user.id)
    )

    return {
        "message": "Your personal schedule",
        "user_id": str(current_user.id),
        "schedules": my_schedules,
    }


@router.get("/manifest")
async def get_daily_manifest(
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_resource_access(ResourceType.MANIFEST)),
) -> dict[str, Any]:
    """Get today's daily manifest.

    Accessible by:
    - Admin
    - Coordinator
    - Clinical Staff (RN, LPN, MSA)

    Returns:
        Today's staff manifest
    """
    manifest = [
        {
            "location": "Main Clinic",
            "time": "AM",
            "staff": [
                {"name": "Dr. Smith", "role": "Attending"},
                {"name": "Dr. Jones", "role": "Resident"},
            ],
        },
        {
            "location": "ICU",
            "time": "AM",
            "staff": [
                {"name": "Dr. Williams", "role": "Attending"},
            ],
        },
    ]

    return {
        "message": "Today's manifest",
        "date": "2025-01-15",
        "locations": manifest,
    }


@router.get("/compliance")
async def get_compliance_report(
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_resource_access(ResourceType.COMPLIANCE)),
) -> dict[str, Any]:
    """Get compliance report (admin only).

    Accessible by:
    - Admin

    Blocked for:
    - Coordinator
    - Faculty
    - Clinical Staff

    Returns:
        Compliance report data
    """
    compliance_data = {
        "status": "compliant",
        "violations": [],
        "acgme_80_hour_compliance": 100.0,
        "supervision_compliance": 100.0,
    }

    return {
        "message": "Compliance report (admin only)",
        "data": compliance_data,
    }


@router.post("/users")
async def create_user(
    username: str,
    email: str,
    role: str,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> dict[str, Any]:
    """Create a new user (admin only).

    Only admins can create new users.

    Args:
        username: New user's username
        email: New user's email
        role: New user's role

    Returns:
        Created user information
    """
    # Validate role
    try:
        RoleFilterService.get_role_from_string(role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role: {role}"
        )

    return {
        "message": "User created (admin only endpoint)",
        "user": {
            "username": username,
            "email": email,
            "role": role,
        },
    }


@router.get("/roles")
async def list_roles() -> dict[str, Any]:
    """List all available roles with their permissions.

    Public endpoint - shows all role types and their access levels.

    Returns:
        Dictionary of all roles and their descriptions
    """
    roles = {}
    for role in UserRole:
        roles[role.value] = RoleFilterService.get_role_description(role)

    return {
        "message": "All available roles",
        "roles": roles,
    }


@router.get("/access-check/{endpoint_category}")
async def check_access(
    endpoint_category: str, current_user: User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """Check if current user can access a specific endpoint category.

    Args:
        endpoint_category: The endpoint category to check (e.g., 'schedules', 'compliance')

    Returns:
        Access check result
    """
    can_access = RoleFilterService.can_access_endpoint(
        current_user.role, endpoint_category
    )

    return {
        "user_role": current_user.role,
        "endpoint_category": endpoint_category,
        "can_access": can_access,
        "message": f"{'Access granted' if can_access else 'Access denied'} to {endpoint_category}",
    }
