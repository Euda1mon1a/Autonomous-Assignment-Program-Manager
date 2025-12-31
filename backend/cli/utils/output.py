"""
Output formatting utilities for CLI.

Provides:
- Table formatting with Rich
- JSON output
- YAML output
- Progress indicators
- Status messages
"""

import json
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box

console = Console()


def print_table(
    data: list[dict[str, Any]],
    title: str | None = None,
    columns: list[str] | None = None,
) -> None:
    """
    Print data as a formatted table.

    Args:
        data: List of dictionaries to display
        title: Optional table title
        columns: Optional list of columns to display (in order)
    """
    if not data:
        console.print("[yellow]No data to display[/yellow]")
        return

    # Determine columns
    if columns is None:
        columns = list(data[0].keys())

    # Create table
    table = Table(title=title, box=box.ROUNDED)

    # Add columns
    for col in columns:
        table.add_column(col.replace("_", " ").title(), style="cyan")

    # Add rows
    for row in data:
        table.add_row(*[str(row.get(col, "")) for col in columns])

    console.print(table)


def print_json(data: Any, indent: int = 2) -> None:
    """Print data as formatted JSON."""
    console.print_json(json.dumps(data, indent=indent, default=str))


def print_yaml(data: Any) -> None:
    """Print data as YAML."""
    console.print(yaml.dump(data, default_flow_style=False))


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def print_panel(content: str, title: str, style: str = "blue") -> None:
    """Print content in a panel."""
    panel = Panel(content, title=title, border_style=style)
    console.print(panel)


def print_tree(data: dict[str, Any], title: str = "Tree") -> None:
    """Print hierarchical data as a tree."""
    tree = Tree(title)

    def add_branches(parent, data_dict):
        for key, value in data_dict.items():
            if isinstance(value, dict):
                branch = parent.add(f"[bold]{key}[/bold]")
                add_branches(branch, value)
            elif isinstance(value, list):
                branch = parent.add(f"[bold]{key}[/bold]")
                for item in value:
                    if isinstance(item, dict):
                        add_branches(branch, item)
                    else:
                        branch.add(str(item))
            else:
                parent.add(f"{key}: {value}")

    add_branches(tree, data)
    console.print(tree)


def print_system_info() -> None:
    """Print system information."""
    import platform
    import sys
    from datetime import datetime

    from cli import __version__
    from cli.config import get_config

    config = get_config()

    info_data = {
        "CLI Version": __version__,
        "Python Version": sys.version.split()[0],
        "Platform": platform.platform(),
        "Profile": config.profile,
        "API URL": config.api_url,
        "Database URL": config.database_url.split("@")[-1],  # Hide credentials
        "Current Time": datetime.now().isoformat(),
    }

    table = Table(title="System Information", box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    for key, value in info_data.items():
        table.add_row(key, str(value))

    console.print(table)


def format_bytes(bytes_size: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}h"
