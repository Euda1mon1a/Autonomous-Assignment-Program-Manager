"""
Progress bar and status utilities for CLI.

Provides:
- Progress bars for long operations
- Spinners for indeterminate tasks
- Status updates
- Task tracking
"""

from typing import Optional, Callable, Any
from contextlib import contextmanager

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

console = Console()


@contextmanager
def progress_bar(description: str = "Processing", total: Optional[int] = None):
    """
    Context manager for progress bar.

    Usage:
        with progress_bar("Loading data", total=100) as progress:
            task = progress.add_task(description, total=100)
            for i in range(100):
                progress.update(task, advance=1)

    Args:
        description: Task description
        total: Total number of steps (None for indeterminate)
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        yield progress


@contextmanager
def spinner(message: str = "Processing..."):
    """
    Context manager for spinner (indeterminate progress).

    Usage:
        with spinner("Loading data"):
            # Do work
            pass

    Args:
        message: Status message to display
    """
    spinner_obj = Spinner("dots", text=message)
    with Live(spinner_obj, console=console, transient=True):
        yield


def run_with_progress(
    func: Callable,
    items: list,
    description: str = "Processing",
    item_name: str = "item",
) -> list:
    """
    Run a function on a list of items with progress bar.

    Args:
        func: Function to apply to each item
        items: List of items to process
        description: Progress bar description
        item_name: Name for individual items

    Returns:
        List of results
    """
    results = []

    with progress_bar(description, total=len(items)) as progress:
        task = progress.add_task(description, total=len(items))

        for i, item in enumerate(items, 1):
            progress.update(
                task,
                description=f"{description} ({i}/{len(items)} {item_name}s)",
                advance=1,
            )
            result = func(item)
            results.append(result)

    return results


class StatusTracker:
    """Track multiple tasks with status updates."""

    def __init__(self, title: str = "Tasks"):
        """Initialize status tracker."""
        self.title = title
        self.tasks = {}
        self._current_id = 0

    def add_task(self, description: str, total: Optional[int] = None) -> int:
        """Add a new task to track."""
        task_id = self._current_id
        self._current_id += 1

        self.tasks[task_id] = {
            "description": description,
            "total": total,
            "completed": 0,
            "status": "pending",
        }

        return task_id

    def update(
        self,
        task_id: int,
        completed: Optional[int] = None,
        status: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Update task status."""
        if task_id in self.tasks:
            if completed is not None:
                self.tasks[task_id]["completed"] = completed
            if status is not None:
                self.tasks[task_id]["status"] = status
            if description is not None:
                self.tasks[task_id]["description"] = description

    def complete(self, task_id: int):
        """Mark task as complete."""
        self.update(task_id, status="complete")

    def fail(self, task_id: int, error: str):
        """Mark task as failed."""
        self.update(task_id, status="failed")
        self.tasks[task_id]["error"] = error

    def display(self):
        """Display current task status."""
        from rich.table import Table

        table = Table(title=self.title)
        table.add_column("Task", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Progress", style="green")

        for task_id, task in self.tasks.items():
            status = task["status"]
            if status == "complete":
                status_str = "[green]✓ Complete[/green]"
            elif status == "failed":
                status_str = "[red]✗ Failed[/red]"
            elif status == "running":
                status_str = "[yellow]⟳ Running[/yellow]"
            else:
                status_str = "[dim]○ Pending[/dim]"

            if task["total"]:
                progress = f"{task['completed']}/{task['total']}"
            else:
                progress = str(task.get("completed", "-"))

            table.add_row(
                task["description"],
                status_str,
                progress,
            )

        console.print(table)


@contextmanager
def step(description: str):
    """
    Context manager for a single step with status.

    Usage:
        with step("Loading configuration"):
            config = load_config()

    Args:
        description: Step description
    """
    console.print(f"[cyan]→[/cyan] {description}...", end="")

    try:
        yield
        console.print(" [green]✓[/green]")
    except Exception as e:
        console.print(f" [red]✗ {str(e)}[/red]")
        raise
