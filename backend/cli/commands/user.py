"""
User management command group.

Commands:
- create: Create new user
- list: List users
- update: Update user information
- delete: Delete user
- roles: Manage user roles
- audit: Show user audit log
- activate/deactivate: Toggle user status
"""

import typer
from rich.console import Console

app = typer.Typer(help="User management commands")
console = Console()


@app.callback()
def callback():
    """User management operations."""
    pass


@app.command()
def whoami():
    """Show current user information."""
    from cli.utils.auth import AuthManager

    auth = AuthManager()
    user_info = auth.get_user_info()

    if user_info:
        console.print(f"[bold]Logged in as:[/bold] {user_info['email']}")
        console.print(f"[bold]Session expires:[/bold] {user_info['expires_at']}")
    else:
        console.print("[yellow]Not logged in[/yellow]")


@app.command()
def login(
    email: str = typer.Option(..., "--email", "-e", prompt=True, help="Email address"),
    password: str = typer.Option(
        ..., "--password", "-p", prompt=True, hide_input=True, help="Password"
    ),
):
    """
    Login to the system.

    Args:
        email: User email
        password: User password
    """
    from cli.utils.auth import AuthManager
    from cli.config import get_config

    config = get_config()
    auth = AuthManager()

    auth.login(email, password, config.api_url)


@app.command()
def logout():
    """Logout from the system."""
    from cli.utils.auth import AuthManager

    auth = AuthManager()
    auth.logout()
