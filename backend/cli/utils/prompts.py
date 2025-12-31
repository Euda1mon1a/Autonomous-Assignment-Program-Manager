"""
Interactive prompt utilities for CLI.

Provides:
- Confirmation prompts
- Input validation
- Multi-choice selection
- Password input
"""

from typing import Any, List, Optional, Callable

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt

console = Console()


def confirm(message: str, default: bool = False) -> bool:
    """
    Ask for confirmation.

    Args:
        message: Confirmation message
        default: Default value if user presses Enter

    Returns:
        True if user confirms, False otherwise
    """
    return Confirm.ask(message, default=default)


def prompt(
    message: str,
    default: str | None = None,
    password: bool = False,
    validator: Callable[[str], bool] | None = None,
) -> str:
    """
    Prompt for input with optional validation.

    Args:
        message: Prompt message
        default: Default value
        password: Hide input if True
        validator: Optional validation function

    Returns:
        User input string
    """
    while True:
        value = Prompt.ask(
            message,
            default=default,
            password=password,
        )

        if validator is None or validator(value):
            return value

        console.print("[red]Invalid input. Please try again.[/red]")


def prompt_int(
    message: str,
    default: int | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """
    Prompt for integer input.

    Args:
        message: Prompt message
        default: Default value
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Integer value
    """
    while True:
        value = IntPrompt.ask(message, default=default)

        if min_value is not None and value < min_value:
            console.print(f"[red]Value must be at least {min_value}[/red]")
            continue

        if max_value is not None and value > max_value:
            console.print(f"[red]Value must be at most {max_value}[/red]")
            continue

        return value


def choose(
    message: str,
    choices: list[str],
    default: str | None = None,
) -> str:
    """
    Prompt user to choose from a list of options.

    Args:
        message: Prompt message
        choices: List of available choices
        default: Default choice

    Returns:
        Selected choice
    """
    # Display choices
    console.print(f"\n{message}")
    for i, choice in enumerate(choices, 1):
        console.print(f"  {i}. {choice}")

    # Get selection
    while True:
        selection = Prompt.ask(
            "Select option",
            default=str(choices.index(default) + 1) if default else None,
        )

        try:
            index = int(selection) - 1
            if 0 <= index < len(choices):
                return choices[index]
        except ValueError:
            # Check if user typed the choice directly
            if selection in choices:
                return selection

        console.print("[red]Invalid selection. Please try again.[/red]")


def confirm_dangerous(
    action: str,
    resource: str,
    confirmation_text: str | None = None,
) -> bool:
    """
    Confirm dangerous action with typed confirmation.

    Args:
        action: Action being performed (e.g., "delete")
        resource: Resource being affected
        confirmation_text: Text user must type (default: resource name)

    Returns:
        True if confirmed, False otherwise
    """
    if confirmation_text is None:
        confirmation_text = resource

    console.print(
        f"\n[bold red]WARNING:[/bold red] You are about to {action} [bold]{resource}[/bold]"
    )
    console.print(f"Type [bold]{confirmation_text}[/bold] to confirm:")

    user_input = Prompt.ask("Confirmation")

    if user_input == confirmation_text:
        return True

    console.print("[yellow]Action cancelled.[/yellow]")
    return False


def prompt_email(message: str = "Email", default: str | None = None) -> str:
    """Prompt for email address with validation."""
    import re

    email_pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    def validate_email(email: str) -> bool:
        if not email_pattern.match(email):
            console.print("[red]Invalid email address[/red]")
            return False
        return True

    return prompt(message, default=default, validator=validate_email)


def prompt_date(
    message: str = "Date (YYYY-MM-DD)",
    default: str | None = None,
) -> str:
    """Prompt for date with validation."""
    from datetime import datetime

    def validate_date(date_str: str) -> bool:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD[/red]")
            return False

    return prompt(message, default=default, validator=validate_date)
