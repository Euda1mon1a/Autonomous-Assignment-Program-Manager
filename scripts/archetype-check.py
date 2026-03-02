#!/usr/bin/env python3
"""
Mind Flayer's Probe — AST-based archetype enforcement for scheduling constraints.

Parses constraint files using Python's ast module and checks for anti-patterns
that have caused real bugs:

ARCH-001 (Phantasm):     resident_idx in call-related constraint (dead code)
ARCH-002 (Lich's Trap):  Constraint initializes solver variable dict
ARCH-003 (Doppelganger): Call constraint uses context.faculty instead of
                         call_eligible_faculty
ARCH-004 (Silent Killer): add_to_cpsat() missing constraint count logging

Usage:
    python3 scripts/archetype-check.py [--staged] [files...]

Exit codes:
    0 - All checks pass (warnings don't block)
    1 - Error-level violations found

Suppression:
    Add # @archetype-ok comment on the flagged line.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ANSI colors (matching project hook conventions)
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
MAGENTA = "\033[0;35m"
NC = "\033[0m"

CONSTRAINT_DIR = Path("backend/app/scheduling/constraints")
EXCLUDED_FILES = {"__init__.py", "base.py", "config.py", "manager.py"}


@dataclass
class Violation:
    file: str
    line: int
    rule: str
    message: str
    fix: str = ""
    severity: str = "error"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_lines(filepath: str) -> list[str]:
    """Cache-friendly line reader for suppression checks."""
    with open(filepath) as f:
        return f.readlines()


_line_cache: dict[str, list[str]] = {}


def _has_suppression(filepath: str, lineno: int) -> bool:
    """Check if a source line has # @archetype-ok suppression."""
    if filepath not in _line_cache:
        _line_cache[filepath] = _read_lines(filepath)
    lines = _line_cache[filepath]
    if lineno <= 0 or lineno > len(lines):
        return False
    return "@archetype-ok" in lines[lineno - 1]


def _get_constraint_classes(tree: ast.Module) -> list[ast.ClassDef]:
    """Find all top-level classes that inherit from HardConstraint or SoftConstraint."""
    constraint_bases = {"HardConstraint", "SoftConstraint"}
    classes = []
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            base_name = None
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr
            if base_name in constraint_bases:
                classes.append(node)
                break
    return classes


def _is_call_related_class(class_node: ast.ClassDef) -> bool:
    """
    Determine if a constraint class operates on call variables.

    A class is call-related if:
    1. It has constraint_type=ConstraintType.CALL in __init__, OR
    2. It accesses variables["call_assignments"] or variables.get("call_assignments")
    """
    for node in ast.walk(class_node):
        # Check __init__ for constraint_type=ConstraintType.CALL
        if isinstance(node, ast.keyword) and node.arg == "constraint_type":
            if isinstance(node.value, ast.Attribute) and node.value.attr == "CALL":
                return True

        # Check for variables.get("call_assignments", ...)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "get" and node.args:
                if (
                    isinstance(node.args[0], ast.Constant)
                    and node.args[0].value == "call_assignments"
                ):
                    return True

        # Check for variables["call_assignments"]
        if isinstance(node, ast.Subscript):
            if (
                isinstance(node.slice, ast.Constant)
                and node.slice.value == "call_assignments"
            ):
                return True

    return False


def _get_solver_methods(class_node: ast.ClassDef) -> list[ast.FunctionDef]:
    """Get add_to_cpsat and add_to_pulp methods from a class."""
    methods = []
    for node in ast.iter_child_nodes(class_node):
        if isinstance(node, ast.FunctionDef) and node.name in (
            "add_to_cpsat",
            "add_to_pulp",
        ):
            methods.append(node)
    return methods


def _is_context_attr(node: ast.AST, attr_name: str) -> bool:
    """Check if node is context.<attr_name> (via Name or parameter)."""
    if not isinstance(node, ast.Attribute) or node.attr != attr_name:
        return False
    # context.attr_name
    if isinstance(node.value, ast.Name) and node.value.id == "context":
        return True
    # self.context.attr_name or similar
    if isinstance(node.value, ast.Attribute) and node.value.attr == "context":
        return True
    return False


# ---------------------------------------------------------------------------
# ARCH-001: resident_idx in call-related constraint
# ---------------------------------------------------------------------------


def check_resident_idx_in_call_constraint(
    tree: ast.Module, filepath: str
) -> list[Violation]:
    """
    Detect context.resident_idx in call-related constraint classes.

    resident_idx maps RESIDENT UUIDs to solver indices. Faculty UUIDs
    are never in resident_idx, so .get(faculty_id) always returns None,
    making the entire code path dead.
    """
    violations = []

    for class_node in _get_constraint_classes(tree):
        if not _is_call_related_class(class_node):
            continue

        for child in ast.walk(class_node):
            if _is_context_attr(child, "resident_idx"):
                if not _has_suppression(filepath, child.lineno):
                    violations.append(
                        Violation(
                            file=filepath,
                            line=child.lineno,
                            rule="ARCH-001",
                            message=(
                                "context.resident_idx in call-related constraint. "
                                "Faculty UUIDs are not in resident_idx — "
                                ".get(faculty_id) always returns None (dead code)."
                            ),
                            fix="Use context.call_eligible_faculty_idx instead",
                        )
                    )

    return violations


# ---------------------------------------------------------------------------
# ARCH-002: Variable dict initialization
# ---------------------------------------------------------------------------


def check_variable_initialization(
    tree: ast.Module, filepath: str
) -> list[Violation]:
    """
    Detect initialization of solver variable dicts in constraint code.

    Constraints must READ existing variables created by the solver.
    Initializing variables["call_assignments"] = {} erases solver vars.
    """
    violations = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:
            if not isinstance(target, ast.Subscript):
                continue

            # Check: variables["call_assignments"] = ...
            is_var_sub = isinstance(target.value, ast.Name) and target.value.id in (
                "variables",
                "vars",
            )
            is_call_key = (
                isinstance(target.slice, ast.Constant)
                and target.slice.value == "call_assignments"
            )

            if not (is_var_sub and is_call_key):
                continue

            # Check if value is empty dict {} or dict()
            is_empty = False
            if isinstance(node.value, ast.Dict) and not node.value.keys:
                is_empty = True
            if (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "dict"
                and not node.value.args
            ):
                is_empty = True

            if is_empty and not _has_suppression(filepath, node.lineno):
                violations.append(
                    Violation(
                        file=filepath,
                        line=node.lineno,
                        rule="ARCH-002",
                        message=(
                            'variables["call_assignments"] initialized to empty dict. '
                            "Solver (solvers.py) owns variable creation. "
                            "Constraints must read, not create."
                        ),
                        fix='Use variables.get("call_assignments", {}) to read safely',
                    )
                )

    return violations


# ---------------------------------------------------------------------------
# ARCH-003: Wrong faculty source for call constraints
# ---------------------------------------------------------------------------


def check_wrong_faculty_source(
    tree: ast.Module, filepath: str
) -> list[Violation]:
    """
    Detect bare iteration over context.faculty in call-related constraints.

    Call constraints must use context.call_eligible_faculty (excludes adjuncts).
    The fallback pattern `context.call_eligible_faculty or context.faculty`
    is valid and NOT flagged.
    """
    violations = []

    for class_node in _get_constraint_classes(tree):
        if not _is_call_related_class(class_node):
            continue

        for method in _get_solver_methods(class_node):
            for node in ast.walk(method):
                if not isinstance(node, ast.For):
                    continue

                iter_node = node.iter

                # Flag: `for x in context.faculty:`
                if _is_context_attr(iter_node, "faculty"):
                    if not _has_suppression(filepath, node.lineno):
                        violations.append(
                            Violation(
                                file=filepath,
                                line=node.lineno,
                                rule="ARCH-003",
                                message=(
                                    "Call constraint iterates context.faculty "
                                    "(includes adjuncts). Use call_eligible_faculty."
                                ),
                                fix=(
                                    "call_eligible = context.call_eligible_faculty "
                                    "or context.faculty"
                                ),
                            )
                        )

    return violations


# ---------------------------------------------------------------------------
# ARCH-004: Missing constraint count logging
# ---------------------------------------------------------------------------


def check_missing_constraint_logging(
    tree: ast.Module, filepath: str
) -> list[Violation]:
    """
    Check that add_to_cpsat() methods contain logging.

    A constraint that adds 0 constraints is likely dead code. Logging
    makes this visible during schedule generation.
    """
    violations = []

    for class_node in _get_constraint_classes(tree):
        for method in ast.iter_child_nodes(class_node):
            if not isinstance(method, ast.FunctionDef):
                continue
            if method.name != "add_to_cpsat":
                continue

            has_logging = False
            for node in ast.walk(method):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                # logger.info(...), logger.debug(...), logger.warning(...)
                if (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "logger"
                    and func.attr in ("info", "debug", "warning")
                ):
                    has_logging = True
                    break

            if not has_logging and not _has_suppression(filepath, method.lineno):
                violations.append(
                    Violation(
                        file=filepath,
                        line=method.lineno,
                        rule="ARCH-004",
                        message=(
                            "add_to_cpsat() has no logging. Log constraint count "
                            "to detect dead code (0 constraints = likely bug)."
                        ),
                        fix='logger.info(f"Added {count} [Name] constraints")',
                        severity="warning",
                    )
                )

    return violations


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def get_files_to_check(args: list[str]) -> list[Path]:
    """Get constraint files to check. Supports --staged flag."""
    if "--staged" in args:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
        )
        files = [
            Path(f)
            for f in result.stdout.strip().split("\n")
            if f.startswith(str(CONSTRAINT_DIR)) and f.endswith(".py")
        ]
    else:
        # Check all constraint files or specific files passed as args
        explicit = [a for a in args[1:] if not a.startswith("--")]
        if explicit:
            files = [Path(a) for a in explicit]
        else:
            files = sorted(CONSTRAINT_DIR.rglob("*.py"))

    return [
        f
        for f in files
        if f.name not in EXCLUDED_FILES
        and "/templates/" not in str(f)
        and f.exists()
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    files = get_files_to_check(sys.argv)
    if not files:
        return 0

    print(f"{MAGENTA}Mind Flayer's Probe: Scanning constraint archetypes...{NC}")

    all_violations: list[Violation] = []

    for filepath in files:
        try:
            source = filepath.read_text()
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError as e:
            print(f"{RED}SYNTAX ERROR: {filepath}:{e.lineno}: {e.msg}{NC}")
            all_violations.append(
                Violation(
                    file=str(filepath),
                    line=e.lineno or 0,
                    rule="PARSE",
                    message=f"SyntaxError: {e.msg}",
                )
            )
            continue

        _line_cache.pop(str(filepath), None)  # Clear stale cache

        all_violations.extend(
            check_resident_idx_in_call_constraint(tree, str(filepath))
        )
        all_violations.extend(check_variable_initialization(tree, str(filepath)))
        all_violations.extend(check_wrong_faculty_source(tree, str(filepath)))
        all_violations.extend(check_missing_constraint_logging(tree, str(filepath)))

    # Report
    errors = 0
    warnings = 0
    for v in all_violations:
        color = RED if v.severity == "error" else YELLOW
        tag = "ERROR" if v.severity == "error" else "WARN"
        print(f"{color}[{tag}] {v.rule}: {v.file}:{v.line}: {v.message}{NC}")
        if v.fix:
            print(f"  {CYAN}Fix: {v.fix}{NC}")

        if v.severity == "error":
            errors += 1
        else:
            warnings += 1

    # Summary
    checked = len(files)
    if errors > 0:
        print()
        print(
            f"{RED}FAILED: {errors} error(s), {warnings} warning(s) "
            f"in {checked} file(s){NC}"
        )
        print(f"{YELLOW}Suppress false positives with: # @archetype-ok{NC}")
        return 1
    elif warnings > 0:
        print()
        print(
            f"{YELLOW}PASSED with {warnings} warning(s) in {checked} file(s){NC}"
        )
        return 0
    else:
        print(f"{GREEN}PASSED: {checked} constraint file(s) match archetypes{NC}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
