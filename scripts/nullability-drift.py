#!/usr/bin/env python3
"""
ARCH-007: Nullability Drift Detector (Phantom Null)

Compares manual TypeScript interfaces in api.ts against generated types
in api-generated.ts to find fields where the manual type strips nullability
that the API actually returns.

Example drift:
  api-generated.ts:  maxSupervisionRatio: number | null;
  api.ts:            maxSupervisionRatio: number;      // DRIFT!

At runtime the API returns null, but TypeScript thinks it's non-nullable,
so .toString() or other operations crash without warning.

Usage:
    python3 scripts/nullability-drift.py [--staged]

Exit codes:
    0 - No drift found
    1 - Nullability drift detected

Suppression:
    Add // @nullable-ok comment on the line in api.ts
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# ANSI colors
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
MAGENTA = "\033[0;35m"
NC = "\033[0m"

MANUAL_TYPES = Path("frontend/src/types/api.ts")
GENERATED_TYPES = Path("frontend/src/types/api-generated.ts")

# Regex to extract interface fields: "  fieldName: type;"  or "  fieldName?: type;"
FIELD_RE = re.compile(
    r"^\s+(\w+)(\??):\s*(.+?)\s*;?\s*(?://.*)?$"
)

# Regex to match exported interface/type declarations (manual api.ts)
INTERFACE_RE = re.compile(
    r"^export\s+(?:interface|type)\s+(\w+)"
)

# Regex to match generated schema types (indented, in components.schemas)
# Format: "        SchemaName: {"
GENERATED_SCHEMA_RE = re.compile(
    r"^\s{8}(\w+): \{$"
)


@dataclass
class NullDrift:
    interface: str
    field: str
    manual_type: str
    generated_type: str
    line: int
    file: str


def parse_manual_interfaces(content: str) -> dict[str, dict[str, str]]:
    """Parse exported TypeScript interfaces from api.ts."""
    interfaces: dict[str, dict[str, str]] = {}
    current_iface: str | None = None
    brace_depth = 0

    for line in content.splitlines():
        m = INTERFACE_RE.match(line)
        if m:
            current_iface = m.group(1)
            interfaces[current_iface] = {}
            brace_depth = 0

        if current_iface:
            brace_depth += line.count("{") - line.count("}")

            if brace_depth == 1:
                fm = FIELD_RE.match(line)
                if fm:
                    field_name = fm.group(1)
                    optional = fm.group(2)
                    field_type = fm.group(3).rstrip(";").strip()
                    if optional:
                        field_type = f"{field_type} | undefined"
                    interfaces[current_iface][field_name] = field_type

            if brace_depth <= 0 and current_iface:
                current_iface = None

    return interfaces


def parse_generated_schemas(content: str) -> dict[str, dict[str, str]]:
    """Parse openapi-typescript generated schemas from api-generated.ts.

    Generated format is nested objects at 8-space indent:
        SchemaName: {
            fieldName: type;
            fieldName?: type | null;
        };
    """
    schemas: dict[str, dict[str, str]] = {}
    current_schema: str | None = None
    brace_depth = 0
    schema_start_depth = 0

    for line in content.splitlines():
        # Detect schema start (8-space indent)
        if current_schema is None:
            m = GENERATED_SCHEMA_RE.match(line)
            if m:
                current_schema = m.group(1)
                schemas[current_schema] = {}
                brace_depth = 1
                schema_start_depth = 1
                continue

        if current_schema:
            brace_depth += line.count("{") - line.count("}")

            # Extract fields at depth 1 relative to schema start
            if brace_depth == schema_start_depth:
                fm = FIELD_RE.match(line)
                if fm:
                    field_name = fm.group(1)
                    optional = fm.group(2)
                    field_type = fm.group(3).rstrip(";").strip()
                    if optional:
                        field_type = f"{field_type} | undefined"
                    schemas[current_schema][field_name] = field_type

            if brace_depth <= 0:
                current_schema = None

    return schemas


def normalize_type(t: str) -> set[str]:
    """Split a union type into its components."""
    return {part.strip() for part in t.split("|") if part.strip()}


def type_is_nullable(t: str) -> bool:
    """Check if a type includes null."""
    return "null" in normalize_type(t)


def find_nullability_drift(
    manual_path: Path, generated_path: Path
) -> list[NullDrift]:
    """Compare manual and generated interfaces for nullability mismatches."""
    manual_content = manual_path.read_text()
    generated_content = generated_path.read_text()

    manual_ifaces = parse_manual_interfaces(manual_content)
    generated_schemas = parse_generated_schemas(generated_content)

    drifts: list[NullDrift] = []

    # Build line number map for manual file
    line_map: dict[str, dict[str, int]] = {}
    current_iface = None
    for i, line in enumerate(manual_content.splitlines(), 1):
        m = INTERFACE_RE.match(line)
        if m:
            current_iface = m.group(1)
            line_map[current_iface] = {}
        if current_iface:
            fm = FIELD_RE.match(line)
            if fm:
                line_map[current_iface][fm.group(1)] = i
            if line.strip() == "}":
                current_iface = None

    manual_lines = manual_content.splitlines()

    # Skip request/mutation types — only response types cause runtime crashes.
    # Create/Update schemas have optional+null meaning "don't send" vs "clear",
    # which is a valid pattern, not a drift bug.
    request_suffixes = ("Create", "Update", "Request", "Params", "Filter")

    for iface_name, manual_fields in manual_ifaces.items():
        # Skip request types (false positives)
        if iface_name.endswith(request_suffixes):
            continue

        # Match manual interface to generated schema
        # Try: exact name, then +Response, +Read suffixes
        gen_fields = None
        for suffix in ["", "Response", "Read"]:
            candidate = f"{iface_name}{suffix}" if suffix else iface_name
            if candidate in generated_schemas:
                gen_fields = generated_schemas[candidate]
                break

        if gen_fields is None:
            continue

        for field_name, manual_type in manual_fields.items():
            if field_name not in gen_fields:
                continue

            gen_type = gen_fields[field_name]

            # Drift: generated says nullable, manual says non-nullable
            if type_is_nullable(gen_type) and not type_is_nullable(manual_type):
                lineno = line_map.get(iface_name, {}).get(field_name, 0)

                # Check suppression
                if 0 < lineno <= len(manual_lines):
                    if "@nullable-ok" in manual_lines[lineno - 1]:
                        continue

                drifts.append(
                    NullDrift(
                        interface=iface_name,
                        field=field_name,
                        manual_type=manual_type,
                        generated_type=gen_type,
                        line=lineno,
                        file=str(manual_path),
                    )
                )

    return drifts


def should_run(args: list[str]) -> bool:
    """Check if api.ts is in staged files (when run as pre-commit hook)."""
    if "--staged" in args:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
        )
        staged = result.stdout.strip()
        return str(MANUAL_TYPES) in staged
    return True


def main() -> int:
    if not should_run(sys.argv):
        return 0

    if not MANUAL_TYPES.exists():
        print(f"{YELLOW}[ARCH-007] {MANUAL_TYPES} not found — skipping{NC}")
        return 0

    if not GENERATED_TYPES.exists():
        print(f"{YELLOW}[ARCH-007] {GENERATED_TYPES} not found — skipping{NC}")
        return 0

    print(f"{MAGENTA}Phantom Null: Checking nullability drift...{NC}")

    drifts = find_nullability_drift(MANUAL_TYPES, GENERATED_TYPES)

    if not drifts:
        print(f"{GREEN}ARCH-007: No nullability drift detected{NC}")
        return 0

    print()
    for d in drifts:
        print(
            f"{RED}[ARCH-007] {d.file}:{d.line}: "
            f"{d.interface}.{d.field}{NC}"
        )
        print(f"  Manual:    {d.manual_type}")
        print(f"  Generated: {d.generated_type}")
        print(
            f"  {CYAN}Fix: Add ' | null' to the manual type, "
            f"or suppress with // @nullable-ok{NC}"
        )
        print()

    print(
        f"{RED}ARCH-007: {len(drifts)} nullability drift(s) found. "
        f"Manual types in api.ts strip null that the API returns.{NC}"
    )
    print(
        f"{YELLOW}This causes runtime crashes when code calls "
        f".toString() or similar on null values.{NC}"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
