#!/usr/bin/env python3
"""
Stack Health Audit Script.

Performs comprehensive codebase and infrastructure health checks:
- Frontend: TypeScript type-check, ESLint, build
- Backend: Ruff linting, mypy type-check (if configured)
- Infrastructure: Alembic migration state, Docker container health

Writes timestamped reports to .claude/dontreadme/stack-health/

Exit codes:
- 0: GREEN (all checks pass)
- 1: YELLOW (warnings only)
- 2: RED (errors present)

Usage:
    python scripts/ops/stack_audit.py
    python scripts/ops/stack_audit.py --quick        # Skip build check
    python scripts/ops/stack_audit.py --json         # JSON output instead of markdown
    python scripts/ops/stack_audit.py --no-report    # Don't write report file
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Project root detection
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"
REPORT_DIR = PROJECT_ROOT / ".claude" / "dontreadme" / "stack-health"


@dataclass
class CheckResult:
    """Result of a single check."""
    name: str
    status: str  # "pass", "warn", "fail", "skip", "error"
    count: int = 0
    details: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    duration_ms: int = 0


@dataclass
class AuditReport:
    """Complete audit report."""
    timestamp: datetime
    status: str  # "GREEN", "YELLOW", "RED"
    checks: Dict[str, CheckResult] = field(default_factory=dict)
    previous_run: Optional[Dict[str, int]] = None
    trends: Dict[str, str] = field(default_factory=dict)  # "improving", "worsening", "stable"


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout: int = 300,
    capture_output: bool = True
) -> Tuple[int, str, str]:
    """Run a command and return (return_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
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


def check_frontend_typecheck() -> CheckResult:
    """Run frontend TypeScript type-check."""
    import time
    start = time.time()

    if not FRONTEND_DIR.exists():
        return CheckResult(
            name="Frontend Type Check",
            status="skip",
            error_message="Frontend directory not found"
        )

    # Check if node_modules exists
    if not (FRONTEND_DIR / "node_modules").exists():
        return CheckResult(
            name="Frontend Type Check",
            status="skip",
            error_message="node_modules not found - run 'npm install'"
        )

    code, stdout, stderr = run_command(
        ["npm", "run", "type-check"],
        cwd=FRONTEND_DIR,
        timeout=120
    )

    duration_ms = int((time.time() - start) * 1000)
    output = stdout + stderr

    # Parse TypeScript errors
    # Pattern: src/file.tsx(line,col): error TS####: message
    error_pattern = r"^(.+\.tsx?)\((\d+),(\d+)\):\s*error\s+TS\d+:"
    errors = []

    for line in output.split("\n"):
        if re.search(error_pattern, line):
            errors.append(line.strip())
        # Also catch Next.js style errors
        elif "error TS" in line.lower() or "Type error:" in line:
            errors.append(line.strip())

    error_count = len(errors)

    if code == 0:
        return CheckResult(
            name="Frontend Type Check",
            status="pass",
            count=0,
            duration_ms=duration_ms
        )
    else:
        return CheckResult(
            name="Frontend Type Check",
            status="fail",
            count=error_count if error_count > 0 else 1,
            details=errors[:50],  # Limit to first 50 errors
            duration_ms=duration_ms
        )


def check_frontend_lint() -> CheckResult:
    """Run frontend ESLint."""
    import time
    start = time.time()

    if not FRONTEND_DIR.exists():
        return CheckResult(
            name="Frontend Lint",
            status="skip",
            error_message="Frontend directory not found"
        )

    if not (FRONTEND_DIR / "node_modules").exists():
        return CheckResult(
            name="Frontend Lint",
            status="skip",
            error_message="node_modules not found"
        )

    code, stdout, stderr = run_command(
        ["npm", "run", "lint"],
        cwd=FRONTEND_DIR,
        timeout=120
    )

    duration_ms = int((time.time() - start) * 1000)
    output = stdout + stderr

    # Count ESLint warnings and errors
    warnings = 0
    errors = 0
    details = []

    # ESLint summary line: "X problems (Y errors, Z warnings)"
    summary_match = re.search(r"(\d+)\s+problems?\s+\((\d+)\s+errors?,\s+(\d+)\s+warnings?\)", output)
    if summary_match:
        errors = int(summary_match.group(2))
        warnings = int(summary_match.group(3))

    # Collect individual issues (lines starting with file paths)
    for line in output.split("\n"):
        if re.match(r"^\s*/|^\s*\./|^\s*src/", line) or "error" in line.lower() or "warning" in line.lower():
            details.append(line.strip())

    if code == 0 and errors == 0:
        status = "pass" if warnings == 0 else "warn"
        return CheckResult(
            name="Frontend Lint",
            status=status,
            count=warnings,
            details=details[:30],
            duration_ms=duration_ms
        )
    else:
        return CheckResult(
            name="Frontend Lint",
            status="fail",
            count=errors,
            details=details[:50],
            duration_ms=duration_ms
        )


def check_frontend_build(skip: bool = False) -> CheckResult:
    """Run frontend build."""
    import time

    if skip:
        return CheckResult(
            name="Frontend Build",
            status="skip",
            error_message="Skipped (--quick mode)"
        )

    start = time.time()

    if not FRONTEND_DIR.exists():
        return CheckResult(
            name="Frontend Build",
            status="skip",
            error_message="Frontend directory not found"
        )

    if not (FRONTEND_DIR / "node_modules").exists():
        return CheckResult(
            name="Frontend Build",
            status="skip",
            error_message="node_modules not found"
        )

    code, stdout, stderr = run_command(
        ["npm", "run", "build"],
        cwd=FRONTEND_DIR,
        timeout=300
    )

    duration_ms = int((time.time() - start) * 1000)
    output = stdout + stderr

    if code == 0:
        return CheckResult(
            name="Frontend Build",
            status="pass",
            count=0,
            duration_ms=duration_ms
        )
    else:
        # Extract error messages
        details = []
        for line in output.split("\n"):
            if "error" in line.lower() or "Error:" in line:
                details.append(line.strip())

        return CheckResult(
            name="Frontend Build",
            status="fail",
            count=len(details) if details else 1,
            details=details[:30],
            error_message="Build failed",
            duration_ms=duration_ms
        )


def check_backend_lint() -> CheckResult:
    """Run backend Ruff linter."""
    import time
    start = time.time()

    if not BACKEND_DIR.exists():
        return CheckResult(
            name="Backend Lint (Ruff)",
            status="skip",
            error_message="Backend directory not found"
        )

    code, stdout, stderr = run_command(
        ["ruff", "check", "."],
        cwd=BACKEND_DIR,
        timeout=60
    )

    duration_ms = int((time.time() - start) * 1000)
    output = stdout + stderr

    if code == -2:  # Command not found
        return CheckResult(
            name="Backend Lint (Ruff)",
            status="skip",
            error_message="ruff not installed",
            duration_ms=duration_ms
        )

    # Count ruff issues
    # Ruff output format: file.py:line:col: CODE message
    issues = []
    for line in output.split("\n"):
        if re.match(r".+\.py:\d+:\d+:", line):
            issues.append(line.strip())

    issue_count = len(issues)

    # Also check for "Found X errors" summary
    found_match = re.search(r"Found\s+(\d+)\s+errors?", output)
    if found_match:
        issue_count = int(found_match.group(1))

    if code == 0:
        return CheckResult(
            name="Backend Lint (Ruff)",
            status="pass",
            count=0,
            duration_ms=duration_ms
        )
    else:
        return CheckResult(
            name="Backend Lint (Ruff)",
            status="fail",
            count=issue_count if issue_count > 0 else 1,
            details=issues[:50],
            duration_ms=duration_ms
        )


def check_backend_typecheck() -> CheckResult:
    """Run backend mypy type-check if configured."""
    import time
    start = time.time()

    if not BACKEND_DIR.exists():
        return CheckResult(
            name="Backend Type Check (mypy)",
            status="skip",
            error_message="Backend directory not found"
        )

    # Check if mypy.ini or pyproject.toml with mypy config exists
    has_mypy_config = (
        (BACKEND_DIR / "mypy.ini").exists() or
        (BACKEND_DIR / ".mypy.ini").exists() or
        (PROJECT_ROOT / "mypy.ini").exists()
    )

    # Even without config, we can still run mypy
    code, stdout, stderr = run_command(
        ["mypy", "app/", "--ignore-missing-imports", "--no-error-summary"],
        cwd=BACKEND_DIR,
        timeout=180
    )

    duration_ms = int((time.time() - start) * 1000)
    output = stdout + stderr

    if code == -2:  # Command not found
        return CheckResult(
            name="Backend Type Check (mypy)",
            status="skip",
            error_message="mypy not installed",
            duration_ms=duration_ms
        )

    # Count mypy errors
    # mypy output: file.py:line: error: message
    errors = []
    for line in output.split("\n"):
        if ": error:" in line:
            errors.append(line.strip())

    error_count = len(errors)

    if code == 0 or error_count == 0:
        return CheckResult(
            name="Backend Type Check (mypy)",
            status="pass",
            count=0,
            duration_ms=duration_ms
        )
    else:
        return CheckResult(
            name="Backend Type Check (mypy)",
            status="warn" if error_count < 10 else "fail",
            count=error_count,
            details=errors[:50],
            duration_ms=duration_ms
        )


def check_migration_state() -> CheckResult:
    """Check Alembic migration state."""
    import time
    start = time.time()

    if not BACKEND_DIR.exists():
        return CheckResult(
            name="Migration State",
            status="skip",
            error_message="Backend directory not found"
        )

    details = []
    issues = 0

    # Check heads (latest migration in code)
    code_heads, stdout_heads, stderr_heads = run_command(
        ["alembic", "heads"],
        cwd=BACKEND_DIR,
        timeout=30
    )

    duration_ms = int((time.time() - start) * 1000)

    if code_heads == -2:
        return CheckResult(
            name="Migration State",
            status="skip",
            error_message="alembic not installed",
            duration_ms=duration_ms
        )

    if code_heads != 0:
        return CheckResult(
            name="Migration State",
            status="error",
            error_message=f"alembic heads failed: {stderr_heads}",
            duration_ms=duration_ms
        )

    heads = stdout_heads.strip().split("\n") if stdout_heads.strip() else []
    details.append(f"Heads: {', '.join(heads) if heads else 'none'}")

    # Check current (what's applied to DB)
    code_current, stdout_current, stderr_current = run_command(
        ["alembic", "current"],
        cwd=BACKEND_DIR,
        timeout=30
    )

    duration_ms = int((time.time() - start) * 1000)

    if code_current != 0:
        # Database might not be running - this is a warning, not error
        details.append("Current: Unable to check (database may not be running)")
        issues += 1
    else:
        current = stdout_current.strip() if stdout_current.strip() else "none"
        details.append(f"Current: {current}")

        # Check if there are pending migrations
        if heads and current:
            # Extract revision IDs
            head_ids = [h.split()[0] for h in heads if h]
            current_ids = [c.split()[0] for c in current.split("\n") if c]

            if head_ids and current_ids:
                if set(head_ids) != set(current_ids):
                    details.append("WARNING: Pending migrations detected")
                    issues += 1

    # Check for multiple heads (branching)
    if len(heads) > 1:
        details.append("WARNING: Multiple heads detected (migration branching)")
        issues += 1

    if issues == 0:
        return CheckResult(
            name="Migration State",
            status="pass",
            count=0,
            details=details,
            duration_ms=duration_ms
        )
    else:
        return CheckResult(
            name="Migration State",
            status="warn",
            count=issues,
            details=details,
            duration_ms=duration_ms
        )


def check_api_health() -> CheckResult:
    """Check API endpoint health and data integrity (antigravity recommendations)."""
    import time
    import urllib.request
    import urllib.error
    start = time.time()

    details = []
    issues = 0
    api_base = "http://localhost:8000"

    # Check 1: API is responding
    try:
        req = urllib.request.Request(f"{api_base}/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                details.append("Health endpoint: OK")
            else:
                details.append(f"Health endpoint: HTTP {response.status}")
                issues += 1
    except urllib.error.URLError as e:
        details.append(f"Health endpoint: UNREACHABLE ({e.reason})")
        issues += 1
        # If API is down, skip remaining checks
        return CheckResult(
            name="API Health",
            status="fail",
            count=issues,
            details=details,
            error_message="API not reachable",
            duration_ms=int((time.time() - start) * 1000)
        )
    except Exception as e:
        details.append(f"Health endpoint: ERROR ({e})")
        issues += 1

    # Check 2: CORS headers present
    try:
        req = urllib.request.Request(f"{api_base}/health", method="OPTIONS")
        req.add_header("Origin", "http://localhost:3000")
        with urllib.request.urlopen(req, timeout=5) as response:
            cors_header = response.headers.get("access-control-allow-origin", "")
            if cors_header:
                details.append(f"CORS headers: OK ({cors_header})")
            else:
                details.append("CORS headers: MISSING")
                issues += 1
    except Exception as e:
        details.append(f"CORS check: SKIPPED ({e})")

    # Check 3: Blocks API returns data
    try:
        req = urllib.request.Request(f"{api_base}/api/v1/blocks?limit=5", method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if isinstance(data, list):
                block_count = len(data)
            elif isinstance(data, dict) and "items" in data:
                block_count = len(data["items"])
            else:
                block_count = 0

            if block_count > 0:
                details.append(f"Blocks API: OK ({block_count} returned for limit=5)")
            else:
                details.append("Blocks API: EMPTY (no blocks returned)")
                issues += 1
    except urllib.error.HTTPError as e:
        details.append(f"Blocks API: HTTP {e.code}")
        issues += 1
    except Exception as e:
        details.append(f"Blocks API: ERROR ({e})")
        issues += 1

    # Check 4: Pagination works correctly
    try:
        req = urllib.request.Request(f"{api_base}/api/v1/assignments?limit=10", method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if isinstance(data, dict):
                total = data.get("total", 0)
                items = data.get("items", [])
                if len(items) <= 10:
                    details.append(f"Pagination: OK (limit=10 returned {len(items)}, total={total})")
                else:
                    details.append(f"Pagination: BROKEN (limit=10 returned {len(items)} items)")
                    issues += 1
            else:
                details.append("Pagination: SKIPPED (unexpected response format)")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            details.append("Pagination: SKIPPED (auth required)")
        else:
            details.append(f"Pagination: HTTP {e.code}")
            issues += 1
    except Exception as e:
        details.append(f"Pagination: ERROR ({e})")

    # Check 5: Rotation templates have valid activity_types
    try:
        req = urllib.request.Request(f"{api_base}/api/v1/rotation-templates?limit=100", method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if isinstance(data, dict) and "items" in data:
                templates = data["items"]
            elif isinstance(data, list):
                templates = data
            else:
                templates = []

            valid_types = {"clinic", "inpatient", "procedure", "procedures", "conference",
                          "education", "outpatient", "absence", "off", "recovery", "elective", "call"}
            invalid = []
            for t in templates:
                activity = t.get("activity_type", "")
                if activity and activity not in valid_types:
                    invalid.append(f"{t.get('name', 'unknown')}: {activity}")

            if invalid:
                details.append(f"Schema validation: {len(invalid)} invalid activity_types")
                details.extend([f"  - {i}" for i in invalid[:5]])
                issues += 1
            else:
                details.append(f"Schema validation: OK ({len(templates)} templates checked)")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            details.append("Schema validation: SKIPPED (auth required)")
        else:
            details.append(f"Schema validation: HTTP {e.code}")
    except Exception as e:
        details.append(f"Schema validation: ERROR ({e})")

    duration_ms = int((time.time() - start) * 1000)

    if issues == 0:
        return CheckResult(
            name="API Health",
            status="pass",
            count=0,
            details=details,
            duration_ms=duration_ms
        )
    else:
        return CheckResult(
            name="API Health",
            status="warn" if issues < 3 else "fail",
            count=issues,
            details=details,
            duration_ms=duration_ms
        )


def check_sacred_backups() -> CheckResult:
    """Check that sacred backups exist before major changes."""
    import time
    start = time.time()

    backup_dir = PROJECT_ROOT / "backups"
    details = []
    issues = 0

    if not backup_dir.exists():
        return CheckResult(
            name="Sacred Backups",
            status="warn",
            count=1,
            details=["Backup directory does not exist"],
            error_message="No backups/ directory found",
            duration_ms=int((time.time() - start) * 1000)
        )

    # Check for sacred backups
    sacred_backups = list(backup_dir.glob("sacred_*.dump")) + list(backup_dir.glob("sacred_*.sql"))
    regular_backups = list(backup_dir.glob("*.dump")) + list(backup_dir.glob("*.sql"))

    # Filter out sacred from regular
    regular_backups = [b for b in regular_backups if "sacred" not in b.name]

    if sacred_backups:
        # Find most recent
        sacred_backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        most_recent = sacred_backups[0]
        age_hours = (time.time() - most_recent.stat().st_mtime) / 3600
        size_mb = most_recent.stat().st_size / (1024 * 1024)

        details.append(f"Sacred backups: {len(sacred_backups)} found")
        details.append(f"Most recent: {most_recent.name} ({size_mb:.1f} MB, {age_hours:.1f}h ago)")

        if age_hours > 168:  # Older than 1 week
            details.append("WARNING: Most recent sacred backup is over 1 week old")
            issues += 1
    else:
        details.append("Sacred backups: NONE FOUND")
        issues += 1

    # Also check regular backups
    if regular_backups:
        details.append(f"Regular backups: {len(regular_backups)} found")
    else:
        details.append("Regular backups: none found")

    duration_ms = int((time.time() - start) * 1000)

    if issues == 0:
        return CheckResult(
            name="Sacred Backups",
            status="pass",
            count=len(sacred_backups),
            details=details,
            duration_ms=duration_ms
        )
    else:
        return CheckResult(
            name="Sacred Backups",
            status="warn",
            count=issues,
            details=details,
            duration_ms=duration_ms
        )


def check_alembic_sync() -> CheckResult:
    """Verify alembic current matches alembic heads (antigravity recommendation)."""
    import time
    start = time.time()

    if not BACKEND_DIR.exists():
        return CheckResult(
            name="Alembic Head Sync",
            status="skip",
            error_message="Backend directory not found"
        )

    details = []
    use_docker = False

    # Try local alembic first, fall back to docker
    code_test, _, stderr_test = run_command(["which", "alembic"], timeout=5)
    if code_test != 0:
        # Check if docker backend container is available
        code_docker, _, _ = run_command(
            ["docker", "compose", "ps", "-q", "backend"],
            cwd=PROJECT_ROOT,
            timeout=10
        )
        if code_docker == 0:
            use_docker = True
            details.append("Using Docker container for alembic checks")
        else:
            return CheckResult(
                name="Alembic Head Sync",
                status="skip",
                error_message="alembic not available locally and backend container not running",
                duration_ms=int((time.time() - start) * 1000)
            )

    # Get heads
    if use_docker:
        code_heads, stdout_heads, stderr_heads = run_command(
            ["docker", "compose", "exec", "-T", "backend", "alembic", "heads"],
            cwd=PROJECT_ROOT,
            timeout=30
        )
    else:
        code_heads, stdout_heads, stderr_heads = run_command(
            ["alembic", "heads"],
            cwd=BACKEND_DIR,
            timeout=30
        )

    if code_heads != 0:
        return CheckResult(
            name="Alembic Head Sync",
            status="error",
            error_message=f"alembic heads failed: {stderr_heads}",
            duration_ms=int((time.time() - start) * 1000)
        )

    # Get current
    if use_docker:
        code_current, stdout_current, stderr_current = run_command(
            ["docker", "compose", "exec", "-T", "backend", "alembic", "current"],
            cwd=PROJECT_ROOT,
            timeout=30
        )
    else:
        code_current, stdout_current, stderr_current = run_command(
            ["alembic", "current"],
            cwd=BACKEND_DIR,
            timeout=30
        )

    duration_ms = int((time.time() - start) * 1000)

    if code_current != 0:
        return CheckResult(
            name="Alembic Head Sync",
            status="warn",
            count=1,
            details=["Cannot check current (database may not be running)"],
            error_message="Database not accessible",
            duration_ms=duration_ms
        )

    # Parse and compare
    heads = [h.split()[0] for h in stdout_heads.strip().split("\n") if h.strip()]
    current_lines = [c for c in stdout_current.strip().split("\n") if c.strip()]
    current = [c.split()[0] for c in current_lines if c and not c.startswith("INFO")]

    details.append(f"Heads: {', '.join(heads)}")
    details.append(f"Current: {', '.join(current) if current else 'none'}")

    # Check for multiple heads (branching)
    if len(heads) > 1:
        details.append("WARNING: Multiple heads detected - migration branching")
        return CheckResult(
            name="Alembic Head Sync",
            status="fail",
            count=len(heads),
            details=details,
            error_message="Multiple migration heads",
            duration_ms=duration_ms
        )

    # Check if current matches head
    if set(heads) == set(current):
        details.append("Sync status: IN SYNC")
        return CheckResult(
            name="Alembic Head Sync",
            status="pass",
            count=0,
            details=details,
            duration_ms=duration_ms
        )
    else:
        details.append("Sync status: OUT OF SYNC - run 'alembic upgrade head'")
        return CheckResult(
            name="Alembic Head Sync",
            status="fail",
            count=1,
            details=details,
            error_message="Database not at head revision",
            duration_ms=duration_ms
        )


def check_docker_health() -> CheckResult:
    """Check Docker container health."""
    import time
    start = time.time()

    code, stdout, stderr = run_command(
        ["docker", "compose", "ps", "--format", "json"],
        cwd=PROJECT_ROOT,
        timeout=30
    )

    duration_ms = int((time.time() - start) * 1000)

    if code == -2:
        return CheckResult(
            name="Docker Containers",
            status="skip",
            error_message="docker not installed",
            duration_ms=duration_ms
        )

    if code != 0:
        # Docker might not be running
        return CheckResult(
            name="Docker Containers",
            status="warn",
            count=0,
            error_message="Docker not running or compose file not found",
            duration_ms=duration_ms
        )

    # Parse container statuses
    details = []
    unhealthy = 0
    healthy = 0

    for line in stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            container = json.loads(line)
            name = container.get("Name", "unknown")
            state = container.get("State", "unknown")
            health = container.get("Health", "")

            status_str = f"{name}: {state}"
            if health:
                status_str += f" ({health})"

            details.append(status_str)

            if state != "running" or health == "unhealthy":
                unhealthy += 1
            else:
                healthy += 1
        except json.JSONDecodeError:
            # Fallback for non-JSON output
            details.append(line.strip())

    if unhealthy == 0:
        return CheckResult(
            name="Docker Containers",
            status="pass",
            count=healthy,
            details=details,
            duration_ms=duration_ms
        )
    else:
        return CheckResult(
            name="Docker Containers",
            status="warn" if unhealthy < 2 else "fail",
            count=unhealthy,
            details=details,
            duration_ms=duration_ms
        )


def load_previous_run() -> Optional[Dict[str, int]]:
    """Load the most recent previous report for trend comparison."""
    if not REPORT_DIR.exists():
        return None

    reports = sorted(REPORT_DIR.glob("*.md"), reverse=True)

    # Skip current timestamp pattern (we want previous, not current)
    for report_path in reports[1:]:  # Skip first (most recent)
        try:
            content = report_path.read_text()

            # Parse counts from markdown table
            # | Check | Status | Count | Trend |
            counts = {}
            for line in content.split("\n"):
                if line.startswith("|") and "---" not in line and "Check" not in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 4:
                        check_name = parts[1]
                        try:
                            count = int(parts[3])
                            counts[check_name] = count
                        except (ValueError, IndexError):
                            pass

            if counts:
                return counts
        except Exception:
            continue

    return None


def calculate_trend(current: int, previous: Optional[int]) -> str:
    """Calculate trend between current and previous values."""
    if previous is None:
        return "new"

    if current < previous:
        return "improving"
    elif current > previous:
        return "worsening"
    else:
        return "stable"


def generate_markdown_report(report: AuditReport) -> str:
    """Generate markdown report."""
    lines = []
    lines.append("# Stack Health Audit")
    lines.append("")
    lines.append(f"**Generated:** {report.timestamp.isoformat()}")
    lines.append(f"**Status:** {report.status}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Check | Status | Count | Trend |")
    lines.append("|-------|--------|-------|-------|")

    status_symbols = {
        "pass": "PASS",
        "warn": "WARN",
        "fail": "FAIL",
        "skip": "SKIP",
        "error": "ERROR"
    }

    trend_symbols = {
        "improving": "-N (down)",
        "worsening": "+N (up)",
        "stable": "= (no change)",
        "new": "(new)"
    }

    for name, check in report.checks.items():
        status_str = status_symbols.get(check.status, check.status.upper())

        trend = report.trends.get(name, "new")
        prev = report.previous_run.get(name) if report.previous_run else None

        if trend == "improving" and prev is not None:
            trend_str = f"-{prev - check.count} (down)"
        elif trend == "worsening" and prev is not None:
            trend_str = f"+{check.count - prev} (up)"
        elif trend == "stable":
            trend_str = "= (no change)"
        else:
            trend_str = "(new)"

        lines.append(f"| {check.name} | {status_str} | {check.count} | {trend_str} |")

    lines.append("")
    lines.append("## Details")
    lines.append("")

    for name, check in report.checks.items():
        lines.append(f"### {check.name}")
        lines.append("")

        if check.error_message:
            lines.append(f"**Note:** {check.error_message}")
            lines.append("")

        if check.duration_ms > 0:
            lines.append(f"**Duration:** {check.duration_ms}ms")
            lines.append("")

        if check.details:
            lines.append(f"**Issues ({len(check.details)}):**")
            lines.append("```")
            for detail in check.details[:30]:  # Limit output
                lines.append(detail)
            if len(check.details) > 30:
                lines.append(f"... and {len(check.details) - 30} more")
            lines.append("```")
            lines.append("")

    # Trend Analysis
    if report.previous_run:
        lines.append("## Trend Analysis")
        lines.append("")
        lines.append("Compared to previous run:")
        lines.append("")

        for name, check in report.checks.items():
            prev = report.previous_run.get(name)
            trend = report.trends.get(name, "new")

            if prev is not None:
                diff = check.count - prev
                symbol = "..." if diff == 0 else ("(up)" if diff > 0 else "(down)")
                status = "(WORSENING)" if trend == "worsening" else ("(IMPROVING)" if trend == "improving" else "")
                lines.append(f"- {check.name}: {prev} -> {check.count} ({diff:+d}) {status}")

    lines.append("")
    lines.append("---")
    lines.append("*Generated by scripts/ops/stack_audit.py*")

    return "\n".join(lines)


def run_audit(quick: bool = False) -> AuditReport:
    """Run the complete stack audit."""
    timestamp = datetime.now()

    # Run all checks
    checks = {}

    print("Running stack health audit...")

    print("  [1/10] Frontend type-check...")
    checks["frontend_typecheck"] = check_frontend_typecheck()

    print("  [2/10] Frontend lint...")
    checks["frontend_lint"] = check_frontend_lint()

    print("  [3/10] Frontend build...")
    checks["frontend_build"] = check_frontend_build(skip=quick)

    print("  [4/10] Backend lint (Ruff)...")
    checks["backend_lint"] = check_backend_lint()

    print("  [5/10] Backend type-check (mypy)...")
    checks["backend_typecheck"] = check_backend_typecheck()

    print("  [6/10] Migration state...")
    checks["migration_state"] = check_migration_state()

    print("  [7/10] Alembic head sync...")
    checks["alembic_sync"] = check_alembic_sync()

    print("  [8/10] Docker containers...")
    checks["docker_health"] = check_docker_health()

    print("  [9/10] API health & data integrity...")
    checks["api_health"] = check_api_health()

    print("  [10/10] Sacred backups...")
    checks["sacred_backups"] = check_sacred_backups()

    # Load previous run for comparison
    previous = load_previous_run()

    # Calculate trends
    trends = {}
    for name, check in checks.items():
        prev_count = previous.get(check.name) if previous else None
        trends[name] = calculate_trend(check.count, prev_count)

    # Determine overall status
    has_fail = any(c.status == "fail" for c in checks.values())
    has_warn = any(c.status in ("warn", "error") for c in checks.values())

    if has_fail:
        status = "RED"
    elif has_warn:
        status = "YELLOW"
    else:
        status = "GREEN"

    return AuditReport(
        timestamp=timestamp,
        status=status,
        checks=checks,
        previous_run=previous,
        trends=trends
    )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Stack health audit for codebase and infrastructure"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip slow checks (build)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of markdown"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Don't write report file"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Custom output path for report"
    )

    args = parser.parse_args()

    try:
        # Run audit
        report = run_audit(quick=args.quick)

        # Generate output
        if args.json:
            output_data = {
                "timestamp": report.timestamp.isoformat(),
                "status": report.status,
                "checks": {
                    name: {
                        "name": c.name,
                        "status": c.status,
                        "count": c.count,
                        "details": c.details,
                        "error_message": c.error_message,
                        "duration_ms": c.duration_ms
                    }
                    for name, c in report.checks.items()
                },
                "previous_run": report.previous_run,
                "trends": report.trends
            }
            output = json.dumps(output_data, indent=2)
        else:
            output = generate_markdown_report(report)

        # Print output
        print("")
        print("=" * 70)
        print(f"Stack Health: {report.status}")
        print("=" * 70)

        for name, check in report.checks.items():
            symbol = "PASS" if check.status == "pass" else check.status.upper()
            print(f"  {check.name}: {symbol} ({check.count} issues)")

        print("")

        # Write report file
        if not args.no_report:
            REPORT_DIR.mkdir(parents=True, exist_ok=True)

            if args.output:
                report_path = Path(args.output)
            else:
                timestamp_str = report.timestamp.strftime("%Y-%m-%d_%H%M%S")
                ext = ".json" if args.json else ".md"
                report_path = REPORT_DIR / f"{timestamp_str}{ext}"

            report_path.write_text(output)
            print(f"Report written to: {report_path}")

        # Return exit code based on status
        if report.status == "GREEN":
            return 0
        elif report.status == "YELLOW":
            return 1
        else:  # RED
            return 2

    except KeyboardInterrupt:
        print("\nAborted by user")
        return 130

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())
