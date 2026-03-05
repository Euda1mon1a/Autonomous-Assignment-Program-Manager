"""MCP tools for K2.5 Agent Swarm integration."""

import logging
import os
import subprocess
from datetime import datetime, timedelta, UTC
from pathlib import Path

from .client import get_moonshot_client
from .models import (
    K2SwarmApplyRequest,
    K2SwarmResultResponse,
    K2SwarmSpawnRequest,
    K2SwarmSpawnResponse,
)

logger = logging.getLogger(__name__)


def is_enabled() -> bool:
    """Check if K2.5 swarm integration is enabled."""
    return os.environ.get("K2_SWARM_ENABLED", "").lower() in ("true", "1", "yes")


async def k2_swarm_spawn_task(
    task: str,
    mode: str = "agent_swarm",
    context_files: list[str] | None = None,
    max_tokens: int = 32000,
    output_format: str = "patches",
) -> dict:
    """
    Spawn a K2.5 Agent Swarm task for parallel execution.

    Args:
        task: Task description for the swarm
        mode: "agent" (single) or "agent_swarm" (100 parallel agents)
        context_files: File paths to include as context
        max_tokens: Maximum output tokens
        output_format: "patches", "files", or "analysis"

    Returns:
        Dict with success, task_id, message
    """
    if not is_enabled():
        return {
            "success": False,
            "task_id": "",
            "message": "K2.5 swarm not enabled. Set K2_SWARM_ENABLED=true",
        }

    client = get_moonshot_client()

    try:
        task_id = await client.spawn_task(
            task=task,
            mode=mode,
            context_files=context_files or [],
            max_tokens=max_tokens,
            output_format=output_format,
        )

        return {
            "success": True,
            "task_id": task_id,
            "message": f"Swarm task spawned ({mode})",
            "estimated_completion": (
                datetime.now(UTC) + timedelta(minutes=5)
            ).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to spawn K2.5 swarm task: {e}")
        return {
            "success": False,
            "task_id": "",
            "message": str(e),
        }


async def k2_swarm_get_result(task_id: str) -> dict:
    """
    Get the result of a K2.5 swarm task.

    Args:
        task_id: Task ID from spawn_task

    Returns:
        Dict with status, progress, result, error
    """
    client = get_moonshot_client()
    status = client.get_status(task_id)

    if status == "unknown":
        return {
            "success": False,
            "status": "failed",
            "progress": 0.0,
            "result": None,
            "error": f"Unknown task ID: {task_id}",
        }

    result = client.get_result(task_id)
    error = client.get_error(task_id)

    return {
        "success": status == "completed",
        "status": status,
        "progress": 1.0 if status == "completed" else 0.5 if status == "running" else 0.0,
        "result": result.model_dump() if result else None,
        "error": error or None,
    }


async def k2_swarm_apply_patches(
    task_id: str,
    patch_indices: list[int] | None = None,
    dry_run: bool = True,
) -> dict:
    """
    Apply patches from a completed K2.5 swarm task.

    Args:
        task_id: Task ID with completed patches
        patch_indices: Specific patch indices to apply (None=all)
        dry_run: If True, preview without applying

    Returns:
        Dict with success, applied patches, and any errors
    """
    client = get_moonshot_client()
    result = client.get_result(task_id)

    if not result or not result.patches:
        return {
            "success": False,
            "message": "No patches available for this task",
            "applied": [],
        }

    patches = result.patches
    if patch_indices is not None:
        patches = [
            p for i, p in enumerate(result.patches) if i in patch_indices
        ]

    applied = []
    errors = []

    for patch in patches:
        filepath = Path(patch.filepath)
        if dry_run:
            applied.append({
                "filepath": patch.filepath,
                "action": "would_apply",
                "diff_preview": patch.diff[:500],
            })
        else:
            try:
                # Apply patch using git apply
                proc = subprocess.run(
                    ["git", "apply", "--check", "-"],
                    input=patch.diff,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if proc.returncode == 0:
                    proc = subprocess.run(
                        ["git", "apply", "-"],
                        input=patch.diff,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if proc.returncode == 0:
                        applied.append({
                            "filepath": patch.filepath,
                            "action": "applied",
                        })
                    else:
                        errors.append({
                            "filepath": patch.filepath,
                            "error": proc.stderr,
                        })
                else:
                    errors.append({
                        "filepath": patch.filepath,
                        "error": f"Patch check failed: {proc.stderr}",
                    })
            except Exception as e:
                errors.append({
                    "filepath": patch.filepath,
                    "error": str(e),
                })

    return {
        "success": len(errors) == 0,
        "message": (
            f"{'Would apply' if dry_run else 'Applied'} {len(applied)} patches"
            + (f", {len(errors)} errors" if errors else "")
        ),
        "applied": applied,
        "errors": errors,
        "dry_run": dry_run,
    }
