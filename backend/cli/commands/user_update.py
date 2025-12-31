"""
User update commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_success, print_error, print_info
from cli.utils.prompts import confirm
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def info(
    user_id: str = typer.Argument(..., help="User ID or email"),
    first_name: str = typer.Option(None, "--first-name", help="New first name"),
    last_name: str = typer.Option(None, "--last-name", help="New last name"),
    email: str = typer.Option(None, "--email", help="New email"),
):
    """
    Update user information.

    Args:
        user_id: User ID or email
        first_name: New first name
        last_name: New last name
        email: New email
    """
    updates = {}

    if first_name:
        updates["first_name"] = first_name
    if last_name:
        updates["last_name"] = last_name
    if email:
        updates["email"] = email

    if not updates:
        print_error("No updates specified")
        raise typer.Exit(1)

    asyncio.run(update_user_info(user_id, updates))


@app.command()
def role(
    user_id: str = typer.Argument(..., help="User ID or email"),
    new_role: str = typer.Argument(..., help="New role"),
):
    """
    Update user role.

    Args:
        user_id: User ID or email
        new_role: New role
    """
    from cli.utils.validators import validate_role

    if not validate_role(new_role):
        print_error(f"Invalid role: {new_role}")
        raise typer.Exit(1)

    if not confirm(f"Change role for {user_id} to {new_role}?"):
        console.print("[yellow]Operation cancelled[/yellow]")
        return

    asyncio.run(update_user_role(user_id, new_role))


@app.command()
def pgy(
    user_id: str = typer.Argument(..., help="Resident ID or email"),
    new_level: str = typer.Argument(..., help="New PGY level"),
):
    """
    Update resident PGY level.

    Args:
        user_id: Resident ID or email
        new_level: New PGY level
    """
    from cli.utils.validators import validate_pgy_level

    if not validate_pgy_level(new_level):
        print_error(f"Invalid PGY level: {new_level}")
        raise typer.Exit(1)

    asyncio.run(update_pgy_level(user_id, new_level))


@app.command()
def password(
    user_id: str = typer.Argument(..., help="User ID or email"),
    new_password: str = typer.Option(None, "--password", "-p", prompt=True, hide_input=True, help="New password"),
):
    """
    Reset user password.

    Args:
        user_id: User ID or email
        new_password: New password
    """
    if len(new_password) < 12:
        print_error("Password must be at least 12 characters")
        raise typer.Exit(1)

    asyncio.run(reset_password(user_id, new_password))


@app.command()
def activate(
    user_id: str = typer.Argument(..., help="User ID or email"),
):
    """
    Activate user account.

    Args:
        user_id: User ID or email
    """
    asyncio.run(set_user_active(user_id, True))


@app.command()
def deactivate(
    user_id: str = typer.Argument(..., help="User ID or email"),
):
    """
    Deactivate user account.

    Args:
        user_id: User ID or email
    """
    if not confirm(f"Deactivate user {user_id}?"):
        console.print("[yellow]Operation cancelled[/yellow]")
        return

    asyncio.run(set_user_active(user_id, False))


async def update_user_info(user_id: str, updates: dict):
    """
    Update user information.

    Args:
        user_id: User ID
        updates: Update dictionary
    """
    api = APIClient()

    try:
        print_info(f"Updating user {user_id}...")

        response = api.put(f"/api/v1/users/{user_id}", json=updates)

        print_success("User updated successfully")

    except Exception as e:
        print_error(f"Update failed: {str(e)}")
        raise typer.Exit(1)


async def update_user_role(user_id: str, new_role: str):
    """
    Update user role.

    Args:
        user_id: User ID
        new_role: New role
    """
    api = APIClient()

    try:
        print_info(f"Updating role for {user_id}...")

        response = api.put(
            f"/api/v1/users/{user_id}/role",
            json={"role": new_role.upper()},
        )

        print_success(f"Role updated to {new_role}")

    except Exception as e:
        print_error(f"Role update failed: {str(e)}")
        raise typer.Exit(1)


async def update_pgy_level(user_id: str, new_level: str):
    """
    Update PGY level.

    Args:
        user_id: User ID
        new_level: New PGY level
    """
    api = APIClient()

    try:
        print_info(f"Updating PGY level for {user_id}...")

        response = api.put(
            f"/api/v1/users/{user_id}",
            json={"pgy_level": new_level},
        )

        print_success(f"PGY level updated to {new_level}")

    except Exception as e:
        print_error(f"PGY update failed: {str(e)}")
        raise typer.Exit(1)


async def reset_password(user_id: str, new_password: str):
    """
    Reset user password.

    Args:
        user_id: User ID
        new_password: New password
    """
    api = APIClient()

    try:
        print_info(f"Resetting password for {user_id}...")

        response = api.post(
            f"/api/v1/users/{user_id}/reset-password",
            json={"new_password": new_password},
        )

        print_success("Password reset successfully")

    except Exception as e:
        print_error(f"Password reset failed: {str(e)}")
        raise typer.Exit(1)


async def set_user_active(user_id: str, active: bool):
    """
    Set user active status.

    Args:
        user_id: User ID
        active: Active flag
    """
    api = APIClient()

    try:
        action = "Activating" if active else "Deactivating"
        print_info(f"{action} user {user_id}...")

        response = api.put(
            f"/api/v1/users/{user_id}",
            json={"is_active": active},
        )

        status = "activated" if active else "deactivated"
        print_success(f"User {status}")

    except Exception as e:
        print_error(f"Status update failed: {str(e)}")
        raise typer.Exit(1)
