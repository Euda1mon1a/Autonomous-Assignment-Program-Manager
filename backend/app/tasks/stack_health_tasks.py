"""
Stack Health Check Celery Tasks.

Periodic tasks for monitoring codebase and infrastructure health:
- Frontend type-check, lint, build status
- Backend lint, type-check status
- Migration state
- Docker container health

These tasks complement the operational health checks (database, Redis, Celery)
with code quality and infrastructure state monitoring.

Configuration:
    Added to celery_app.py beat_schedule for periodic execution.
    Default: every 4 hours during development.
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from celery import shared_task

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

# Paths relative to the project
# In Docker, these paths need adjustment
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"
REPORT_DIR = PROJECT_ROOT / ".claude" / "dontreadme" / "stack-health"


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout: int = 120,
) -> Tuple[int, str, str]:
    """Run a command and return (return_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return -2, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return -3, "", str(e)


def check_frontend_typecheck() -> Dict[str, Any]:
    """Check frontend TypeScript compilation."""
    if not FRONTEND_DIR.exists():
        return {"status": "skip", "message": "Frontend directory not found", "count": 0}

    if not (FRONTEND_DIR / "node_modules").exists():
        return {"status": "skip", "message": "node_modules not installed", "count": 0}

    code, stdout, stderr = run_command(
        ["npm", "run", "type-check"],
        cwd=FRONTEND_DIR,
        timeout=120
    )

    output = stdout + stderr

    if code == 0:
        return {"status": "pass", "count": 0}
    else:
        # Count error lines
        error_count = output.count("error TS")
        return {
            "status": "fail",
            "count": error_count if error_count > 0 else 1,
            "sample": output[:500] if output else None
        }


def check_frontend_lint() -> Dict[str, Any]:
    """Check frontend ESLint."""
    if not FRONTEND_DIR.exists():
        return {"status": "skip", "message": "Frontend directory not found", "count": 0}

    if not (FRONTEND_DIR / "node_modules").exists():
        return {"status": "skip", "message": "node_modules not installed", "count": 0}

    code, stdout, stderr = run_command(
        ["npm", "run", "lint"],
        cwd=FRONTEND_DIR,
        timeout=120
    )

    output = stdout + stderr

    # Parse ESLint summary
    import re
    summary = re.search(r"(\d+)\s+problems?\s+\((\d+)\s+errors?,\s+(\d+)\s+warnings?\)", output)

    if summary:
        errors = int(summary.group(2))
        warnings = int(summary.group(3))
    else:
        errors = 0
        warnings = 0

    if code == 0 and errors == 0:
        return {"status": "pass" if warnings == 0 else "warn", "count": warnings}
    else:
        return {"status": "fail", "count": errors}


def check_backend_lint() -> Dict[str, Any]:
    """Check backend Ruff linting."""
    if not BACKEND_DIR.exists():
        return {"status": "skip", "message": "Backend directory not found", "count": 0}

    code, stdout, stderr = run_command(
        ["ruff", "check", "."],
        cwd=BACKEND_DIR,
        timeout=60
    )

    if code == -2:
        return {"status": "skip", "message": "ruff not installed", "count": 0}

    output = stdout + stderr

    # Count issues
    import re
    issues = len(re.findall(r".+\.py:\d+:\d+:", output))

    if code == 0:
        return {"status": "pass", "count": 0}
    else:
        return {"status": "fail", "count": issues if issues > 0 else 1}


def check_migration_state() -> Dict[str, Any]:
    """Check Alembic migration state."""
    if not BACKEND_DIR.exists():
        return {"status": "skip", "message": "Backend directory not found", "count": 0}

    # Check heads
    code_heads, stdout_heads, stderr_heads = run_command(
        ["alembic", "heads"],
        cwd=BACKEND_DIR,
        timeout=30
    )

    if code_heads == -2:
        return {"status": "skip", "message": "alembic not installed", "count": 0}

    if code_heads != 0:
        return {"status": "error", "message": stderr_heads, "count": 1}

    heads = stdout_heads.strip().split("\n") if stdout_heads.strip() else []

    # Check for multiple heads (branching)
    if len(heads) > 1:
        return {
            "status": "warn",
            "message": f"Multiple heads detected: {len(heads)}",
            "count": len(heads) - 1
        }

    # Check current (may fail if DB not running)
    code_current, stdout_current, _ = run_command(
        ["alembic", "current"],
        cwd=BACKEND_DIR,
        timeout=30
    )

    if code_current != 0:
        return {
            "status": "warn",
            "message": "Could not check current migration (DB may be offline)",
            "count": 1
        }

    return {"status": "pass", "count": 0}


def check_docker_health() -> Dict[str, Any]:
    """Check Docker container health."""
    code, stdout, stderr = run_command(
        ["docker", "compose", "ps", "--format", "json"],
        cwd=PROJECT_ROOT,
        timeout=30
    )

    if code == -2:
        return {"status": "skip", "message": "docker not installed", "count": 0}

    if code != 0:
        return {"status": "warn", "message": "Docker not running", "count": 0}

    # Parse container statuses
    unhealthy = 0
    total = 0

    for line in stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            container = json.loads(line)
            total += 1
            state = container.get("State", "")
            health = container.get("Health", "")

            if state != "running" or health == "unhealthy":
                unhealthy += 1
        except json.JSONDecodeError:
            pass

    if unhealthy == 0:
        return {"status": "pass", "count": total}
    else:
        return {"status": "fail", "count": unhealthy}


@shared_task(
    name="app.tasks.stack_health_tasks.stack_health_check",
    bind=True,
    max_retries=1,
    default_retry_delay=60,
    queue="maintenance",
)
def stack_health_check(self, write_report: bool = True) -> Dict[str, Any]:
    """
    Perform stack health check and optionally write report.

    This task checks:
    - Frontend type-check
    - Frontend lint
    - Backend lint (Ruff)
    - Migration state
    - Docker container health

    Args:
        write_report: If True, write markdown report to stack-health directory

    Returns:
        Dict with status, checks, and overall health
    """
    logger.info("Starting stack health check")

    timestamp = datetime.now()
    checks = {}

    # Run checks (skip slow ones like build)
    logger.info("Checking frontend type-check...")
    checks["frontend_typecheck"] = check_frontend_typecheck()

    logger.info("Checking frontend lint...")
    checks["frontend_lint"] = check_frontend_lint()

    logger.info("Checking backend lint...")
    checks["backend_lint"] = check_backend_lint()

    logger.info("Checking migration state...")
    checks["migration_state"] = check_migration_state()

    logger.info("Checking docker health...")
    checks["docker_health"] = check_docker_health()

    # Determine overall status
    has_fail = any(c.get("status") == "fail" for c in checks.values())
    has_warn = any(c.get("status") in ("warn", "error") for c in checks.values())

    if has_fail:
        status = "RED"
    elif has_warn:
        status = "YELLOW"
    else:
        status = "GREEN"

    result = {
        "timestamp": timestamp.isoformat(),
        "status": status,
        "checks": checks,
    }

    # Write report if requested
    if write_report:
        try:
            REPORT_DIR.mkdir(parents=True, exist_ok=True)

            timestamp_str = timestamp.strftime("%Y-%m-%d_%H%M%S")
            report_path = REPORT_DIR / f"{timestamp_str}_celery.md"

            report_content = generate_report(result)
            report_path.write_text(report_content)

            logger.info(f"Stack health report written to: {report_path}")
            result["report_path"] = str(report_path)
        except Exception as e:
            logger.warning(f"Failed to write report: {e}")
            result["report_error"] = str(e)

    # Log summary
    logger.info(f"Stack health check complete: {status}")
    for name, check in checks.items():
        logger.info(f"  {name}: {check.get('status')} ({check.get('count', 0)} issues)")

    # Alert on RED status
    if status == "RED":
        logger.warning("Stack health is RED - errors detected in codebase/infrastructure")
        # Could trigger notification here if notification system is available

    return result


def generate_report(result: Dict[str, Any]) -> str:
    """Generate markdown report from check results."""
    lines = [
        "# Stack Health Audit (Celery)",
        "",
        f"**Generated:** {result['timestamp']}",
        f"**Status:** {result['status']}",
        "",
        "## Summary",
        "",
        "| Check | Status | Issues |",
        "|-------|--------|--------|",
    ]

    check_names = {
        "frontend_typecheck": "Frontend Type Check",
        "frontend_lint": "Frontend Lint",
        "backend_lint": "Backend Lint (Ruff)",
        "migration_state": "Migration State",
        "docker_health": "Docker Containers",
    }

    for key, check in result["checks"].items():
        name = check_names.get(key, key)
        status = check.get("status", "unknown").upper()
        count = check.get("count", 0)
        lines.append(f"| {name} | {status} | {count} |")

    lines.extend([
        "",
        "---",
        "*Generated by Celery task: stack_health_check*",
    ])

    return "\n".join(lines)


@shared_task(
    name="app.tasks.stack_health_tasks.quick_stack_check",
    bind=True,
    max_retries=0,
    queue="maintenance",
)
def quick_stack_check(self) -> Dict[str, Any]:
    """
    Quick stack health check (no report writing, minimal checks).

    Useful for manual invocation or pre-deployment checks.
    Only checks backend lint and migration state (fastest checks).

    Returns:
        Dict with status and key checks only
    """
    logger.info("Starting quick stack check")

    checks = {}

    logger.info("Checking backend lint...")
    checks["backend_lint"] = check_backend_lint()

    logger.info("Checking migration state...")
    checks["migration_state"] = check_migration_state()

    has_fail = any(c.get("status") == "fail" for c in checks.values())
    has_warn = any(c.get("status") in ("warn", "error") for c in checks.values())

    if has_fail:
        status = "RED"
    elif has_warn:
        status = "YELLOW"
    else:
        status = "GREEN"

    logger.info(f"Quick stack check complete: {status}")

    return {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "checks": checks,
    }


# Beat schedule for stack health tasks
STACK_HEALTH_BEAT_SCHEDULE = {
    # Stack health check every 4 hours
    "stack-health-periodic": {
        "task": "app.tasks.stack_health_tasks.stack_health_check",
        "schedule": 14400,  # 4 hours in seconds
        "kwargs": {
            "write_report": True,
        },
        "options": {
            "queue": "maintenance",
            "expires": 3600,
        },
    },
}


def get_stack_health_beat_schedule() -> dict:
    """
    Get beat schedule configuration for stack health tasks.

    Returns:
        Dict with beat schedule configuration

    Usage:
        In celery_app.py:

        from app.tasks.stack_health_tasks import get_stack_health_beat_schedule

        celery_app.conf.beat_schedule.update(
            get_stack_health_beat_schedule()
        )
    """
    return STACK_HEALTH_BEAT_SCHEDULE


def configure_celery_for_stack_health(celery_app_instance):
    """
    Configure Celery app with stack health tasks.

    Args:
        celery_app_instance: Celery application instance

    Usage:
        from app.core.celery_app import celery_app
        from app.tasks.stack_health_tasks import configure_celery_for_stack_health

        configure_celery_for_stack_health(celery_app)
    """
    # Update beat schedule
    celery_app_instance.conf.beat_schedule.update(get_stack_health_beat_schedule())

    # Add task route
    if not hasattr(celery_app_instance.conf, "task_routes"):
        celery_app_instance.conf.task_routes = {}
    celery_app_instance.conf.task_routes.update({
        "app.tasks.stack_health_tasks.*": {"queue": "maintenance"},
    })

    # Ensure maintenance queue exists
    if not hasattr(celery_app_instance.conf, "task_queues"):
        celery_app_instance.conf.task_queues = {}
    celery_app_instance.conf.task_queues.update({
        "maintenance": {},
    })
