"""Role-based view API."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.role_views import StaffRole, RoleViewConfig, ViewPermissions
from app.services.role_view_service import RoleViewService

router = APIRouter()

@router.get("/views/permissions/{role}", response_model=ViewPermissions)
def get_role_permissions(
    role: StaffRole,
    current_user: User = Depends(get_current_active_user)
):
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
def get_role_config(
    role: StaffRole,
    current_user: User = Depends(get_current_active_user)
):
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
def get_current_user_view_config(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get view configuration for current user.

    Returns:
        RoleViewConfig for the authenticated user
    """
    try:
        config = RoleViewService.get_role_config(current_user.role)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user's role configuration: {str(e)}"
        )

@router.post("/views/check-access")
def check_endpoint_access(
    role: StaffRole,
    endpoint_category: str,
    current_user: User = Depends(get_current_active_user)
):
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
def list_all_roles(
    current_user: User = Depends(get_current_active_user)
):
    """
    List all available staff roles.

    Returns:
        List of all StaffRole enum values
    """
    return [role.value for role in StaffRole]

@router.get("/views/permissions", response_model=dict)
def get_all_role_permissions(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get permissions for all roles.

    Returns:
        Dictionary mapping role names to their permissions
    """
    return {
        role.value: RoleViewService.get_permissions(role).dict()
        for role in StaffRole
    }
