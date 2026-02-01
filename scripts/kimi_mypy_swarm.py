#!/usr/bin/env python3
"""
Kimi K2.5 Mypy Swarm Fixer

Orchestrates parallel calls to Moonshot's Kimi K2.5 to fix mypy errors.
Designed for oversight by Claude - validates all fixes before applying.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

# Configuration
API_BASE = "https://api.moonshot.ai/v1"
MODEL = "kimi-k2-turbo-preview"  # Faster, allows temp < 1
MAX_CONCURRENT = 20  # Parallel requests - scale up for swarm
MAX_TOKENS = 8192
MAX_ERRORS_PER_CALL = 10  # Limit errors per API call to avoid overwhelming model
BACKEND_ROOT = Path(__file__).parent.parent / "backend"


@dataclass
class MypyError:
    file: str
    line: int
    code: str
    message: str
    note: str | None = None


@dataclass
class FileErrors:
    file: str
    errors: list[MypyError]
    content: str


def get_api_key() -> str:
    """Get Moonshot API key from macOS Keychain."""
    result = subprocess.run(
        ["security", "find-generic-password", "-a", "moltbot", "-s", "moonshot-ai-api-key", "-w"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Failed to get API key from keychain")
    return result.stdout.strip()


def run_mypy() -> list[MypyError]:
    """Run mypy and parse errors."""
    result = subprocess.run(
        ["mypy", "app", "--no-error-summary"],
        capture_output=True,
        text=True,
        cwd=BACKEND_ROOT,
    )

    errors = []
    current_notes = []

    for line in result.stdout.splitlines():
        # Match error lines: file.py:123: error: message [code]
        match = re.match(r"^(app/[^:]+):(\d+): error: (.+) \[([^\]]+)\]$", line)
        if match:
            if current_notes and errors:
                errors[-1].note = "\n".join(current_notes)
                current_notes = []

            errors.append(MypyError(
                file=match.group(1),
                line=int(match.group(2)),
                message=match.group(3),
                code=match.group(4),
            ))
        elif line.strip().startswith("note:") and errors:
            current_notes.append(line.strip())

    return errors


def group_errors_by_file(errors: list[MypyError]) -> dict[str, list[MypyError]]:
    """Group errors by file path."""
    grouped: dict[str, list[MypyError]] = {}
    for err in errors:
        if err.file not in grouped:
            grouped[err.file] = []
        grouped[err.file].append(err)
    return grouped


def extract_context(content: str, errors: list[MypyError], context_lines: int = 10) -> tuple[str, dict[int, int]]:
    """Extract relevant code sections around errors with line mapping."""
    lines = content.splitlines()
    needed_lines: set[int] = set()

    for err in errors:
        start = max(0, err.line - context_lines - 1)
        end = min(len(lines), err.line + context_lines)
        for i in range(start, end):
            needed_lines.add(i)

    # Build continuous ranges
    sorted_lines = sorted(needed_lines)
    chunks = []
    line_map = {}  # original line -> extracted line

    extracted_line = 1
    prev_line = -2
    for orig_line in sorted_lines:
        if orig_line > prev_line + 1:
            if chunks:
                chunks.append("# ... (code omitted) ...")
                extracted_line += 1
        line_map[orig_line + 1] = extracted_line  # +1 because errors use 1-indexed
        chunks.append(f"{orig_line + 1:4d}| {lines[orig_line]}")
        extracted_line += 1
        prev_line = orig_line

    return "\n".join(chunks), line_map


def build_fix_prompt(file_errors: FileErrors) -> str:
    """Build a prompt for Kimi to fix the errors."""
    # For large files, extract only relevant sections
    if len(file_errors.content.splitlines()) > 500:
        context, line_map = extract_context(file_errors.content, file_errors.errors, context_lines=15)
        file_display = f"(Showing relevant sections only)\n{context}"
    else:
        file_display = file_errors.content

    error_list = "\n".join(
        f"- Line {e.line}: [{e.code}] {e.message}" + (f"\n  {e.note}" if e.note else "")
        for e in file_errors.errors
    )

    return f"""You are a Python type annotation fixer. Fix ONLY the listed mypy errors.

## EXAMPLES

### Example 1: Implicit Optional [assignment]
ERROR: Line 45: [assignment] Incompatible default for argument "x" (default has type "None", argument has type "str")
CODE:
  45|    def foo(self, x: str = None):
OUTPUT:
45|    def foo(self, x: str | None = None):

### Example 2: Wrong builtin type [valid-type]
ERROR: Line 12: [valid-type] Function "builtins.any" is not valid as a type
CODE:
  12|def check(x: any) -> bool:
OUTPUT:
12|def check(x: Any) -> bool:

### Example 3: Incompatible return [return-value]
ERROR: Line 89: [return-value] Incompatible return value type (got "str | None", expected "str")
CODE:
  87|    def get_name(self) -> str:
  88|        if self.name:
  89|            return self.name
  90|        return None
OUTPUT:
87|    def get_name(self) -> str | None:

## RULES
1. Output format: LINE_NUMBER|exact fixed line with original indentation
2. Count leading spaces carefully - preserve exact indentation
3. Only fix errors listed - do not modify other code
4. If you cannot fix safely, output: SKIP|LINE_NUMBER|reason

## ERRORS TO FIX
{error_list}

## CODE (with line numbers)
{file_display}

## YOUR FIXES:"""


async def call_kimi(client: httpx.AsyncClient, api_key: str, prompt: str) -> str:
    """Call Kimi K2.5 API."""
    response = await client.post(
        f"{API_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": MAX_TOKENS,
            "temperature": 0.6,  # Per Moonshot docs for turbo model
            "top_p": 0.95,
        },
        timeout=120.0,
    )
    if response.status_code != 200:
        error_text = response.text
        raise RuntimeError(f"API error {response.status_code}: {error_text[:500]}")
    data = response.json()
    content = data["choices"][0]["message"].get("content", "")
    # Handle reasoning models that may have reasoning_content
    if not content and "reasoning_content" in data["choices"][0]["message"]:
        content = data["choices"][0]["message"]["reasoning_content"]
    return content


def parse_line_fixes(response: str) -> tuple[dict[int, str], list[str]]:
    """Parse line-by-line fixes from response. Returns (fixes, skipped)."""
    fixes = {}
    skipped = []
    for line in response.strip().splitlines():
        # Handle markdown code blocks
        if line.startswith("```") or line.strip() == "":
            continue
        # Handle SKIP responses
        if line.upper().startswith("SKIP|"):
            skipped.append(line)
            continue
        # Parse LINE_NUMBER|code format
        if "|" in line:
            parts = line.split("|", 1)
            try:
                line_num = int(parts[0].strip())
                code = parts[1] if len(parts) > 1 else ""
                fixes[line_num] = code
            except ValueError:
                continue
    return fixes, skipped


def apply_line_fixes(content: str, fixes: dict[int, str]) -> str:
    """Apply line-by-line fixes to content."""
    lines = content.splitlines()
    for line_num, fixed_code in fixes.items():
        if 1 <= line_num <= len(lines):
            lines[line_num - 1] = fixed_code  # Convert to 0-indexed

    result = "\n".join(lines)

    # Add missing imports if needed
    needs_any = "Any" in result and "from typing import" in result and "Any" not in result.split("from typing import")[1].split("\n")[0]
    needs_optional = "Optional[" in result and "Optional" not in result.split("from typing import")[1].split("\n")[0] if "from typing import" in result else False
    needs_callable = "Callable" in result and "from typing import" in result and "Callable" not in result.split("from typing import")[1].split("\n")[0]

    # Simple import addition for common cases
    if "| None" in result and "from __future__ import annotations" not in result:
        # Add future annotations for Python 3.9 compatibility
        if result.startswith('"""'):
            # Find end of docstring
            end = result.find('"""', 3) + 3
            result = result[:end] + "\nfrom __future__ import annotations" + result[end:]
        else:
            result = "from __future__ import annotations\n" + result

    return result


async def fix_file(
    client: httpx.AsyncClient,
    api_key: str,
    file_errors: FileErrors,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Fix a single file's mypy errors."""
    prompt = build_fix_prompt(file_errors)

    try:
        response = await call_kimi(client, api_key, prompt)
        fixes, skipped = parse_line_fixes(response)

        if not fixes and not skipped:
            return {
                "file": file_errors.file,
                "status": "error",
                "message": f"No valid fixes parsed. Response preview: {response[:300]}",
            }

        if not fixes and skipped:
            return {
                "file": file_errors.file,
                "status": "skipped",
                "message": f"All {len(skipped)} errors skipped by model",
                "skipped": skipped,
            }

        # Apply fixes to content
        fixed_code = apply_line_fixes(file_errors.content, fixes)

        # Check for syntax errors in the fix
        try:
            compile(fixed_code, file_errors.file, "exec")
        except SyntaxError as e:
            return {
                "file": file_errors.file,
                "status": "syntax_error",
                "message": str(e),
                "fixes_attempted": len(fixes),
                "fixes": fixes,
            }

        file_path = BACKEND_ROOT / file_errors.file

        if dry_run:
            return {
                "file": file_errors.file,
                "status": "preview",
                "lines_fixed": len(fixes),
                "lines_skipped": len(skipped),
                "errors_targeted": len(file_errors.errors),
                "fixes": fixes,
            }
        else:
            # Write the fixed file
            file_path.write_text(fixed_code)
            return {
                "file": file_errors.file,
                "status": "applied",
                "lines_fixed": len(fixes),
                "lines_skipped": len(skipped),
                "errors_targeted": len(file_errors.errors),
            }

    except Exception as e:
        return {
            "file": file_errors.file,
            "status": "error",
            "message": str(e),
        }


async def run_swarm(
    files: list[FileErrors],
    api_key: str,
    dry_run: bool = True,
    max_concurrent: int = MAX_CONCURRENT,
) -> list[dict[str, Any]]:
    """Run the swarm of parallel fixes."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async with httpx.AsyncClient() as client:
        async def bounded_fix(file_errors: FileErrors) -> dict[str, Any]:
            async with semaphore:
                print(f"  Processing: {file_errors.file} ({len(file_errors.errors)} errors)")
                return await fix_file(client, api_key, file_errors, dry_run)

        results = await asyncio.gather(*[bounded_fix(f) for f in files])

    return list(results)


def main():
    parser = argparse.ArgumentParser(description="Kimi K2.5 Mypy Swarm Fixer")
    parser.add_argument("--apply", action="store_true", help="Apply fixes (default is dry-run)")
    parser.add_argument("--limit", type=int, default=10, help="Max files to process")
    parser.add_argument("--filter", type=str, help="Filter files by pattern (e.g., 'resilience')")
    parser.add_argument("--max-errors", type=int, default=999, help="Only process files with <= N errors")
    parser.add_argument("--min-errors", type=int, default=1, help="Only process files with >= N errors")
    parser.add_argument("--concurrent", type=int, default=MAX_CONCURRENT, help="Max concurrent requests")
    parser.add_argument("--validate", action="store_true", help="Validate fixes reduce errors (slower)")
    args = parser.parse_args()

    print("=" * 60)
    print("Kimi K2.5 Mypy Swarm Fixer")
    print("=" * 60)

    # Get API key
    print("\n[1/5] Getting API key from keychain...")
    api_key = get_api_key()
    print("  ✓ API key loaded")

    # Run mypy
    print("\n[2/5] Running mypy...")
    errors = run_mypy()
    print(f"  ✓ Found {len(errors)} errors")

    # Group by file
    print("\n[3/5] Grouping errors by file...")
    grouped = group_errors_by_file(errors)
    print(f"  ✓ Errors in {len(grouped)} files")

    # Filter by pattern if requested
    if args.filter:
        grouped = {k: v for k, v in grouped.items() if args.filter in k}
        print(f"  ✓ Filtered to {len(grouped)} files matching '{args.filter}'")

    # Filter by error count
    grouped = {k: v for k, v in grouped.items()
               if args.min_errors <= len(v) <= args.max_errors}
    print(f"  ✓ {len(grouped)} files with {args.min_errors}-{args.max_errors} errors")

    # Sort by error count (fewest errors first for higher success rate)
    sorted_files = sorted(grouped.items(), key=lambda x: len(x[1]))

    # Limit files
    selected = sorted_files[:args.limit]
    print(f"\n[4/5] Loading {len(selected)} files...")

    file_errors_list = []
    for file_path, file_errs in selected:
        full_path = BACKEND_ROOT / file_path
        if full_path.exists():
            content = full_path.read_text()
            file_errors_list.append(FileErrors(
                file=file_path,
                errors=file_errs,
                content=content,
            ))
            print(f"  - {file_path}: {len(file_errs)} errors, {len(content.splitlines())} lines")

    # Run swarm
    mode = "APPLY MODE" if args.apply else "DRY RUN"
    print(f"\n[5/5] Running swarm ({mode}, {args.concurrent} concurrent)...")

    results = asyncio.run(run_swarm(
        file_errors_list,
        api_key,
        dry_run=not args.apply,
        max_concurrent=args.concurrent,
    ))

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    success_count = 0
    for r in results:
        status = r["status"]
        file = r["file"]
        skipped = r.get("lines_skipped", 0)
        skip_info = f" ({skipped} skipped)" if skipped else ""

        if status == "preview":
            success_count += 1
            print(f"✓ {file}: {r['lines_fixed']} lines fixed for {r['errors_targeted']} errors{skip_info}")
            if r.get("fixes"):
                for line_num, code in list(r["fixes"].items())[:3]:
                    print(f"    L{line_num}: {code[:60]}...")
                if len(r["fixes"]) > 3:
                    print(f"    ... and {len(r['fixes']) - 3} more fixes")
        elif status == "applied":
            success_count += 1
            print(f"✓ {file}: APPLIED {r['lines_fixed']} fixes ({r['errors_targeted']} errors){skip_info}")
        elif status == "skipped":
            print(f"⊘ {file}: All errors skipped by model")
        elif status == "syntax_error":
            print(f"✗ {file}: Syntax error - {r['message']}")
            if r.get("fixes"):
                for line_num, code in list(r["fixes"].items())[:5]:
                    print(f"    L{line_num}: {code[:70]}...")
        else:
            print(f"✗ {file}: {r.get('message', 'Unknown error')}")

    print(f"\n📊 Success rate: {success_count}/{len(results)} ({100*success_count//len(results) if results else 0}%)")

    if not args.apply:
        print("\n⚠️  DRY RUN - No changes made. Use --apply to apply fixes.")
        print("   Review the results above, then run with --apply if satisfied.")


if __name__ == "__main__":
    main()
