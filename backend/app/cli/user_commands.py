"""User management CLI commands."""

from typing import Optional

import click
from sqlalchemy import select

from app.core.logging import get_logger
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.person import Person
from app.models.user import User

logger = get_logger(__name__)

# Valid roles as defined in the User model
VALID_ROLES = [
    "admin",
    "coordinator",
    "faculty",
    "clinical_staff",
    "rn",
    "lpn",
    "msa",
    "resident",
]


@click.group()
def user() -> None:
    """User management commands."""
    pass


@user.command()
@click.option(
    "--email",
    type=str,
    required=True,
    help="User email address",
)
@click.option(
    "--password",
    type=str,
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="User password (will prompt if not provided)",
)
@click.option(
    "--role",
    type=click.Choice(VALID_ROLES),
    default="resident",
    help="User role",
)
@click.option(
    "--first-name",
    type=str,
    help="First name",
)
@click.option(
    "--last-name",
    type=str,
    help="Last name",
)
@click.option(
    "--active/--inactive",
    default=True,
    help="User active status",
)
def create(
    email: str,
    password: str,
    role: str,
    first_name: str | None,
    last_name: str | None,
    active: bool,
) -> None:
    """
    Create a new user account.

    Example:
        python -m app.cli user create \\
            --email admin@example.com \\
            --role admin \\
            --first-name John \\
            --last-name Doe
    """
    db = SessionLocal()

    try:
        # Check if user already exists
        existing = db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if existing:
            click.echo(f"Error: User with email {email} already exists", err=True)
            raise click.Abort()

        # Generate username from email
        username = email.split("@")[0]

        # Create user
        user_obj = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            role=role,
            is_active=active,
        )
        db.add(user_obj)

        # Create associated person if names provided
        if first_name or last_name:
            person = Person(
                email=email,
                first_name=first_name or "",
                last_name=last_name or "",
                role=role,
            )
            db.add(person)

        db.commit()
        db.refresh(user_obj)

        click.echo("User created successfully")
        click.echo(f"  ID: {user_obj.id}")
        click.echo(f"  Email: {user_obj.email}")
        click.echo(f"  Role: {user_obj.role}")
        click.echo(f"  Active: {user_obj.is_active}")

    except Exception as e:
        logger.error(f"User creation failed: {e}", exc_info=True)
        db.rollback()
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@user.command()
@click.option(
    "--role",
    type=click.Choice(VALID_ROLES),
    help="Filter by role",
)
@click.option(
    "--active/--inactive",
    default=None,
    help="Filter by active status",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
def list(
    role: str | None,
    active: bool | None,
    format: str,
) -> None:
    """
    List all users.

    Example:
        python -m app.cli user list --role resident --active
        python -m app.cli user list --format json
    """
    db = SessionLocal()

    try:
        query = select(User)

        if role:
            query = query.where(User.role == role)

        if active is not None:
            query = query.where(User.is_active == active)

        users = db.execute(query).scalars().all()

        if not users:
            click.echo("No users found")
            return

        if format == "table":
            # Print header
            click.echo(
                f"{'ID':<36} {'Email':<30} {'Role':<15} {'Active':<7} {'Created':<20}"
            )
            click.echo("-" * 110)

            # Print rows
            for u in users:
                click.echo(
                    f"{str(u.id):<36} {u.email:<30} {u.role:<15} "
                    f"{'Y' if u.is_active else 'N':<7} {u.created_at.strftime('%Y-%m-%d %H:%M'):<20}"
                )

            click.echo(f"\nTotal: {len(users)} users")

        elif format == "json":
            import json

            data = [
                {
                    "id": str(u.id),
                    "email": u.email,
                    "role": u.role,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat(),
                }
                for u in users
            ]
            click.echo(json.dumps(data, indent=2))

        elif format == "csv":
            import csv
            import sys

            writer = csv.writer(sys.stdout)
            writer.writerow(["ID", "Email", "Role", "Active", "Created"])

            for u in users:
                writer.writerow(
                    [
                        str(u.id),
                        u.email,
                        u.role,
                        u.is_active,
                        u.created_at.isoformat(),
                    ]
                )

    except Exception as e:
        logger.error(f"User list failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@user.command()
@click.option(
    "--email",
    type=str,
    required=True,
    help="User email address",
)
@click.option(
    "--new-password",
    type=str,
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="New password (will prompt if not provided)",
)
def reset_password(email: str, new_password: str) -> None:
    """
    Reset user password.

    Example:
        python -m app.cli user reset-password --email user@example.com
    """
    db = SessionLocal()

    try:
        user_obj = db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if not user_obj:
            click.echo(f"Error: User not found: {email}", err=True)
            raise click.Abort()

        user_obj.hashed_password = get_password_hash(new_password)
        db.commit()

        click.echo(f"Password reset successfully for {email}")

    except Exception as e:
        logger.error(f"Password reset failed: {e}", exc_info=True)
        db.rollback()
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@user.command()
@click.option(
    "--email",
    type=str,
    required=True,
    help="User email address",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm deletion without prompt",
)
def delete(email: str, confirm: bool) -> None:
    """
    Delete a user account.

    WARNING: This is a destructive operation.

    Example:
        python -m app.cli user delete --email user@example.com
    """
    db = SessionLocal()

    try:
        user_obj = db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if not user_obj:
            click.echo(f"Error: User not found: {email}", err=True)
            raise click.Abort()

        if not confirm:
            if not click.confirm(f"Delete user {email}?"):
                click.echo("Aborted")
                return

        db.delete(user_obj)
        db.commit()

        click.echo(f"User deleted: {email}")

    except Exception as e:
        logger.error(f"User deletion failed: {e}", exc_info=True)
        db.rollback()
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@user.command()
@click.option(
    "--email",
    type=str,
    required=True,
    help="User email address",
)
@click.option(
    "--active/--inactive",
    required=True,
    help="Set active status",
)
def set_active(email: str, active: bool) -> None:
    """
    Set user active/inactive status.

    Example:
        python -m app.cli user set-active --email user@example.com --active
        python -m app.cli user set-active --email user@example.com --inactive
    """
    db = SessionLocal()

    try:
        user_obj = db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if not user_obj:
            click.echo(f"Error: User not found: {email}", err=True)
            raise click.Abort()

        user_obj.is_active = active
        db.commit()

        status = "activated" if active else "deactivated"
        click.echo(f"User {status}: {email}")

    except Exception as e:
        logger.error(f"Status change failed: {e}", exc_info=True)
        db.rollback()
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()
