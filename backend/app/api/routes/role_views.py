"""Role-based view API."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.role_views import StaffRole, RoleViewConfig, ViewPermissions
from app.services.role_view_service import RoleViewService

router = APIRouter()

@router.get("/views/permissions/{role}", response_model=ViewPermissions)
def get_role_permissions(role: StaffRole):
    """
    Get view permissions for a specific role.

    Args:
        role: The staff role to get permissions for

    Returns:
        ViewPermissions object containing all permissions for the role
    """
    try:
        permissions = RoleViewService.get_permissions(role)
        return permissions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve permissions: {str(e)}"
        )

@router.get("/views/config/{role}", response_model=RoleViewConfig)
def get_role_config(role: StaffRole):
    """
    Get complete view configuration for a specific role.

    Args:
        role: The staff role to get configuration for

    Returns:
        RoleViewConfig object containing role and permissions
    """
    try:
        config = RoleViewService.get_role_config(role)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve role configuration: {str(e)}"
        )

@router.get("/views/config")
def get_current_user_view_config():
    """
    Get view configuration for current user.

    Note: This endpoint requires authentication integration.
    Currently returns a placeholder response.

    TODO: Integrate with authentication service to get current user's role

    Returns:
        RoleViewConfig for the authenticated user
    """
    # Placeholder implementation - needs auth integration
    # In a real implementation, you would:
    # 1. Get current user from auth token/session
    # 2. Look up user's role from database
    # 3. Return their role configuration

    # For now, return a sample response
    return {
        "message": "This endpoint requires authentication integration",
        "note": "Integrate with your auth service to retrieve current user's role",
        "example_usage": "GET /views/config/{role} to get config for a specific role"
    }

@router.post("/views/check-access")
def check_endpoint_access(role: StaffRole, endpoint_category: str):
    """
    Check if a role can access a specific endpoint category.

    Args:
        role: The staff role to check
        endpoint_category: Category of endpoint (e.g., 'schedules', 'compliance', 'swaps')

    Returns:
        Dict with access permission and role information
    """
    try:
        can_access = RoleViewService.can_access_endpoint(role, endpoint_category)
        return {
            "role": role,
            "endpoint_category": endpoint_category,
            "can_access": can_access,
            "permissions": RoleViewService.get_permissions(role)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check access: {str(e)}"
        )

@router.get("/views/roles", response_model=list)
def list_all_roles():
    """
    List all available staff roles.

    Returns:
        List of all StaffRole enum values
    """
    return [role.value for role in StaffRole]

@router.get("/views/permissions", response_model=dict)
def get_all_role_permissions():
    """
    Get permissions for all roles.

    Returns:
        Dictionary mapping role names to their permissions
    """
    return {
        role.value: RoleViewService.get_permissions(role).dict()
        for role in StaffRole
    }
