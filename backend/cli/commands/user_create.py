"""
User creation commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_success, print_error, print_info
from cli.utils.prompts import prompt_email, prompt, confirm
from cli.utils.validators import validate_role, validate_pgy_level
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def user(
    email: str = typer.Option(None, "--email", "-e", help="Email address"),
    first_name: str = typer.Option(None, "--first-name", help="First name"),
    last_name: str = typer.Option(None, "--last-name", help="Last name"),
    role: str = typer.Option(None, "--role", "-r", help="User role"),
    pgy_level: str = typer.Option(None, "--pgy", help="PGY level (for residents)"),
    interactive: bool = typer.Option(
        True, "--interactive/--batch", help="Interactive mode"
    ),
):
    """
    Create a new user.

    Args:
        email: Email address
        first_name: First name
        last_name: Last name
        role: User role
        pgy_level: PGY level
        interactive: Interactive mode
    """
    if interactive:
        # Interactive prompts
        if not email:
            email = prompt_email("Email address")

        if not first_name:
            first_name = prompt("First name")

        if not last_name:
            last_name = prompt("Last name")

        if not role:
            from cli.utils.prompts import choose

            role = choose(
                "Select role",
                [
                    "ADMIN",
                    "COORDINATOR",
                    "FACULTY",
                    "RESIDENT",
                    "CLINICAL_STAFF",
                    "RN",
                    "LPN",
                    "MSA",
                ],
            )

        if role == "RESIDENT" and not pgy_level:
            pgy_level = choose("Select PGY level", ["PGY-1", "PGY-2", "PGY-3"])

    # Validate
    if not email or not first_name or not last_name or not role:
        print_error("Missing required fields")
        raise typer.Exit(1)

    if not validate_role(role):
        print_error(f"Invalid role: {role}")
        raise typer.Exit(1)

    if pgy_level and not validate_pgy_level(pgy_level):
        print_error(f"Invalid PGY level: {pgy_level}")
        raise typer.Exit(1)

    asyncio.run(create_user(email, first_name, last_name, role, pgy_level))


@app.command()
def resident(
    email: str = typer.Argument(..., help="Email address"),
    first_name: str = typer.Argument(..., help="First name"),
    last_name: str = typer.Argument(..., help="Last name"),
    pgy_level: str = typer.Argument(..., help="PGY level"),
):
    """
    Create a new resident (shortcut).

    Args:
        email: Email address
        first_name: First name
        last_name: Last name
        pgy_level: PGY level
    """
    asyncio.run(create_user(email, first_name, last_name, "RESIDENT", pgy_level))


@app.command()
def faculty(
    email: str = typer.Argument(..., help="Email address"),
    first_name: str = typer.Argument(..., help="First name"),
    last_name: str = typer.Argument(..., help="Last name"),
):
    """
    Create a new faculty member (shortcut).

    Args:
        email: Email
        first_name: First name
        last_name: Last name
    """
    asyncio.run(create_user(email, first_name, last_name, "FACULTY", None))


@app.command()
def batch(
    file: str = typer.Argument(..., help="CSV file with user data"),
):
    """
    Create users from CSV file.

    CSV format: email,first_name,last_name,role,pgy_level

    Args:
        file: CSV file path
    """
    asyncio.run(create_users_from_csv(file))


async def create_user(
    email: str, first_name: str, last_name: str, role: str, pgy_level: str = None
):
    """
    Create a user via API.

    Args:
        email: Email address
        first_name: First name
        last_name: Last name
        role: User role
        pgy_level: PGY level (optional)
    """
    api = APIClient()

    try:
        print_info(f"Creating user: {email}")

        user_data = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "role": role.upper(),
        }

        if pgy_level:
            user_data["pgy_level"] = pgy_level

        response = api.post("/api/v1/users", json=user_data)

        user_id = response.get("id")
        print_success(f"User created: {email} (ID: {user_id})")

        # Show temporary password if included
        if "temp_password" in response:
            console.print(
                f"\n[yellow]Temporary password:[/yellow] {response['temp_password']}"
            )
            console.print("[dim]User must change password on first login[/dim]")

    except Exception as e:
        print_error(f"User creation failed: {str(e)}")
        raise typer.Exit(1)


async def create_users_from_csv(file_path: str):
    """
    Create users from CSV file.

    Args:
        file_path: CSV file path
    """
    import csv
    from pathlib import Path

    csv_file = Path(file_path)

    if not csv_file.exists():
        print_error(f"File not found: {file_path}")
        raise typer.Exit(1)

    try:
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            users = list(reader)

        console.print(f"Found {len(users)} users in CSV")

        if not confirm(f"Create {len(users)} users?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

        created = 0
        failed = 0

        for user in users:
            try:
                await create_user(
                    email=user["email"],
                    first_name=user["first_name"],
                    last_name=user["last_name"],
                    role=user["role"],
                    pgy_level=user.get("pgy_level"),
                )
                created += 1
            except Exception as e:
                print_error(f"Failed to create {user['email']}: {str(e)}")
                failed += 1

        console.print("\n[bold]Summary:[/bold]")
        console.print(f"Created: {created}")
        console.print(f"Failed: {failed}")

    except Exception as e:
        print_error(f"Batch creation failed: {str(e)}")
        raise typer.Exit(1)
