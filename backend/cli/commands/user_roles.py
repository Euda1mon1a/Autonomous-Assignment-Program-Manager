"""
User role management commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_success, print_error, print_table
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def list():
    """List all available roles."""
    roles = [
        {"role": "ADMIN", "description": "System administrator"},
        {"role": "COORDINATOR", "description": "Program coordinator"},
        {"role": "FACULTY", "description": "Faculty member"},
        {"role": "RESIDENT", "description": "Resident physician"},
        {"role": "CLINICAL_STAFF", "description": "Clinical staff"},
        {"role": "RN", "description": "Registered Nurse"},
        {"role": "LPN", "description": "Licensed Practical Nurse"},
        {"role": "MSA", "description": "Medical Support Assistant"},
    ]

    print_table(roles, title="Available Roles", columns=["role", "description"])


@app.command()
def assign(
    user_id: str = typer.Argument(..., help="User ID or email"),
    role: str = typer.Argument(..., help="Role to assign"),
):
    """
    Assign role to user.

    Args:
        user_id: User ID or email
        role: Role name
    """
    asyncio.run(assign_role(user_id, role))


@app.command()
def remove(
    user_id: str = typer.Argument(..., help="User ID or email"),
    role: str = typer.Argument(..., help="Role to remove"),
):
    """
    Remove role from user.

    Args:
        user_id: User ID or email
        role: Role name
    """
    asyncio.run(remove_role(user_id, role))


@app.command()
def show(
    user_id: str = typer.Argument(..., help="User ID or email"),
):
    """
    Show user's roles.

    Args:
        user_id: User ID or email
    """
    asyncio.run(show_user_roles(user_id))


async def assign_role(user_id: str, role: str):
    """
    Assign role to user.

    Args:
        user_id: User ID
        role: Role name
    """
    from cli.utils.validators import validate_role

    if not validate_role(role):
        print_error(f"Invalid role: {role}")
        raise typer.Exit(1)

    api = APIClient()

    try:
        response = api.post(
            f"/api/v1/users/{user_id}/roles",
            json={"role": role.upper()},
        )

        print_success(f"Role {role} assigned to {user_id}")

    except Exception as e:
        print_error(f"Role assignment failed: {str(e)}")
        raise typer.Exit(1)


async def remove_role(user_id: str, role: str):
    """
    Remove role from user.

    Args:
        user_id: User ID
        role: Role name
    """
    api = APIClient()

    try:
        api.delete(f"/api/v1/users/{user_id}/roles/{role.upper()}")

        print_success(f"Role {role} removed from {user_id}")

    except Exception as e:
        print_error(f"Role removal failed: {str(e)}")
        raise typer.Exit(1)


async def show_user_roles(user_id: str):
    """
    Show user's roles.

    Args:
        user_id: User ID
    """
    api = APIClient()

    try:
        response = api.get(f"/api/v1/users/{user_id}/roles")

        roles = response.get("roles", [])

        if not roles:
            console.print(f"[yellow]No roles assigned to {user_id}[/yellow]")
            return

        console.print(f"\n[bold]Roles for {user_id}:[/bold]")
        for role in roles:
            console.print(f"  • {role}")

    except Exception as e:
        print_error(f"Failed to get roles: {str(e)}")
        raise typer.Exit(1)
