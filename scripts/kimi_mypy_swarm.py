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
MAX_REPAIR_ATTEMPTS = 2  # Generate-Check-Repair loop iterations
BACKEND_ROOT = Path(__file__).parent.parent / "backend"

# Error type tracking for feedback loop
ERROR_STATS: dict[str, dict[str, int]] = {}


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


def run_mypy_on_file(file_path: str) -> list[MypyError]:
    """Run mypy on a single file and return errors."""
    result = subprocess.run(
        ["mypy", file_path, "--no-error-summary"],
        capture_output=True,
        text=True,
        cwd=BACKEND_ROOT,
    )

    errors = []
    for line in result.stdout.splitlines():
        # Match error lines: file.py:123: error: message [code]
        match = re.match(r"^[^:]+:(\d+): error: (.+) \[([^\]]+)\]$", line)
        if match:
            errors.append(MypyError(
                file=file_path,
                line=int(match.group(1)),
                message=match.group(2),
                code=match.group(3),
            ))
    return errors


def validate_indentation(original_content: str, fixed_line: str, line_num: int) -> bool:
    """Verify fix preserves leading whitespace."""
    orig_lines = original_content.splitlines()
    if line_num < 1 or line_num > len(orig_lines):
        return False
    orig_indent = len(orig_lines[line_num - 1]) - len(orig_lines[line_num - 1].lstrip())
    fixed_indent = len(fixed_line) - len(fixed_line.lstrip())
    return orig_indent == fixed_indent


def update_error_stats(error_code: str, success: bool) -> None:
    """Track success rate by mypy error code."""
    if error_code not in ERROR_STATS:
        ERROR_STATS[error_code] = {"success": 0, "fail": 0}
    ERROR_STATS[error_code]["success" if success else "fail"] += 1


def format_file_errors(file_errors: FileErrors, context_lines: int = 5) -> str:
    """Format a single file's errors with relevant code context."""
    lines = file_errors.content.splitlines()
    output = [f"\n### {file_errors.file}"]

    for err in file_errors.errors:
        # Show context around the error
        start = max(0, err.line - context_lines - 1)
        end = min(len(lines), err.line + context_lines)

        output.append(f"\nERROR Line {err.line}: [{err.code}] {err.message}")
        output.append("```python")
        for i in range(start, end):
            marker = ">>>" if i == err.line - 1 else "   "
            output.append(f"{marker} {i+1:4d}| {lines[i]}")
        output.append("```")

    return "\n".join(output)


def build_swarm_prompt(files: list[FileErrors]) -> str:
    """Build a swarm-friendly prompt for batch processing multiple files."""
    # Group all errors by type across all files
    errors_by_type: dict[str, list[tuple[str, MypyError]]] = {}
    for fe in files:
        for err in fe.errors:
            if err.code not in errors_by_type:
                errors_by_type[err.code] = []
            errors_by_type[err.code].append((fe.file, err))

    # Build error category summary
    type_summary = "\n".join(
        f"- [{code}]: {len(errs)} errors across {len(set(f for f, _ in errs))} files"
        for code, errs in sorted(errors_by_type.items(), key=lambda x: -len(x[1]))
    )

    # Format all files with context
    files_content = "\n".join(format_file_errors(fe) for fe in files)

    return f"""## MISSION
Fix mypy type annotation errors across {len(files)} Python files.
Total errors: {sum(len(fe.errors) for fe in files)}

## ERROR CATEGORIES (specialize by type)
{type_summary}

## FIX PATTERNS BY CATEGORY
- [assignment]: Parameter has `= None` but type doesn't allow None → add `| None`
- [return-value]: Return type doesn't match → update return annotation
- [arg-type]: Argument type mismatch → often needs logic change, SKIP if complex
- [valid-type]: Invalid type like `any` → use `Any` from typing
- [override]: Method signature differs from parent → match parent signature
- [attr-defined]: Attribute not defined → SKIP (needs class changes)

## PARALLELIZATION STRATEGY
Process errors by category. For each category, apply the same fix pattern to all matching errors.

## FILES AND ERRORS
{files_content}

## OUTPUT FORMAT (one line per fix)
For fixes: FILE_PATH|LINE_NUMBER|FIXED_CODE
For skips: FILE_PATH|LINE_NUMBER|SKIP|reason

Example:
app/utils/helpers.py|45|    def foo(self, x: str | None = None):
app/models/user.py|123|SKIP|requires logic change

## EXECUTE
Process all {len(files)} files. Output one line per error (fix or skip)."""


def parse_swarm_response(response: str) -> dict[str, dict[int, str]]:
    """Parse swarm batch response into per-file fixes."""
    fixes: dict[str, dict[int, str]] = {}  # file -> {line: code}
    skips: dict[str, dict[int, str]] = {}  # file -> {line: reason}

    for line in response.strip().splitlines():
        # Skip markdown and empty lines
        if line.startswith("```") or not line.strip():
            continue
        if "|" not in line:
            continue

        parts = line.split("|")
        if len(parts) < 3:
            continue

        file_path = parts[0].strip()
        try:
            line_num = int(parts[1].strip())
        except ValueError:
            continue

        if parts[2].strip().upper() == "SKIP":
            reason = parts[3].strip() if len(parts) > 3 else "unspecified"
            if file_path not in skips:
                skips[file_path] = {}
            skips[file_path][line_num] = reason
        else:
            # Everything after line number is the code
            code = "|".join(parts[2:])  # Rejoin in case code contains |
            if file_path not in fixes:
                fixes[file_path] = {}
            fixes[file_path][line_num] = code

    return fixes, skips


async def run_swarm_batch(
    files: list[FileErrors],
    api_key: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Run a single swarm batch call for multiple files."""
    prompt = build_swarm_prompt(files)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": MAX_TOKENS * 2,  # More tokens for batch
                    "temperature": 0.6,
                    "top_p": 0.95,
                },
                timeout=300.0,  # Longer timeout for batch
            )

            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"API error {response.status_code}: {response.text[:500]}",
                }

            data = response.json()
            content = data["choices"][0]["message"].get("content", "")

        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Parse batch response
    fixes, skips = parse_swarm_response(content)

    # Build file content map for applying fixes
    file_content_map = {fe.file: fe.content for fe in files}

    results = []
    total_fixed = 0
    total_skipped = 0
    total_errors = sum(len(fe.errors) for fe in files)

    for fe in files:
        file_fixes = fixes.get(fe.file, {})
        file_skips = skips.get(fe.file, {})

        if not file_fixes and not file_skips:
            results.append({
                "file": fe.file,
                "status": "no_response",
                "errors": len(fe.errors),
            })
            continue

        # Validate and apply fixes
        valid_fixes = {}
        for line_num, code in file_fixes.items():
            if validate_indentation(fe.content, code, line_num):
                valid_fixes[line_num] = code
                update_error_stats(
                    next((e.code for e in fe.errors if e.line == line_num), "unknown"),
                    True
                )
            else:
                # Track rejected fixes
                update_error_stats(
                    next((e.code for e in fe.errors if e.line == line_num), "unknown"),
                    False
                )

        if valid_fixes:
            fixed_content = apply_line_fixes(fe.content, valid_fixes)

            # Syntax check
            try:
                compile(fixed_content, fe.file, "exec")
            except SyntaxError as e:
                results.append({
                    "file": fe.file,
                    "status": "syntax_error",
                    "message": str(e),
                    "fixes_attempted": len(valid_fixes),
                })
                continue

            if not dry_run:
                (BACKEND_ROOT / fe.file).write_text(fixed_content)

            total_fixed += len(valid_fixes)

        total_skipped += len(file_skips)

        results.append({
            "file": fe.file,
            "status": "applied" if not dry_run and valid_fixes else "preview",
            "fixes": len(valid_fixes),
            "skips": len(file_skips),
            "errors": len(fe.errors),
        })

    return {
        "status": "batch_complete",
        "files_processed": len(files),
        "total_errors": total_errors,
        "total_fixed": total_fixed,
        "total_skipped": total_skipped,
        "results": results,
        "raw_response_preview": content[:500] if content else "",
    }


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

    return f"""You are my assistant for fixing Python type annotation errors. I'll show you mypy errors and the relevant code. For each error, think through the fix, then output it.

## How to approach each error:

1. **Read the error message** - it tells you exactly what's wrong
2. **Find the line** - look at the code at that line number
3. **Determine the fix** - usually one of:
   - Add `| None` to allow None values
   - Change `any` to `Any` (capital A)
   - Adjust return type to match what's actually returned
   - Add missing type annotation
4. **Preserve indentation** - count the leading spaces exactly
5. **Output the fix** - format: `LINE_NUMBER|fixed code`

## Examples with reasoning:

### Example 1
ERROR: Line 45: [assignment] Incompatible default for argument "x" (default has type "None", argument has type "str")
CODE:
  45|    def foo(self, x: str = None):

REASONING: The parameter `x` has default `None` but type `str`. To accept None, add `| None`.
FIX: 45|    def foo(self, x: str | None = None):

### Example 2
ERROR: Line 12: [valid-type] Function "builtins.any" is not valid as a type
CODE:
  12|def check(x: any) -> bool:

REASONING: `any` (lowercase) is a function, not a type. Use `Any` (from typing) instead.
FIX: 12|def check(x: Any) -> bool:

### Example 3
ERROR: Line 89: [return-value] Incompatible return value type (got "str | None", expected "str")
CODE:
  87|    def get_name(self) -> str:
  90|        return None

REASONING: Function can return None but declares `-> str`. Change return type to `str | None`.
FIX: 87|    def get_name(self) -> str | None:

### Example 4
ERROR: Line 55: [arg-type] Argument 1 to "process" has incompatible type "str | None"; expected "str"
CODE:
  54|    value = self.get_value()  # returns str | None
  55|    result = process(value)

REASONING: `value` might be None but `process` expects `str`. Need to handle None case.
SKIP: This requires adding an if-check, which changes logic beyond just the line.

## OUTPUT FORMAT

For each error, output ONE of:
- `LINE_NUMBER|fixed code with exact same indentation`
- `SKIP|LINE_NUMBER|reason why this needs more than a type fix`

## ERRORS TO FIX
{error_list}

## CODE
{file_display}

## YOUR FIXES (one per line):"""


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


async def fix_file_with_repair(
    client: httpx.AsyncClient,
    api_key: str,
    file_errors: FileErrors,
    max_attempts: int = MAX_REPAIR_ATTEMPTS,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Fix a file using Generate-Check-Repair loop."""
    original_content = file_errors.content
    current_content = original_content
    current_errors = file_errors.errors
    total_fixes = 0
    all_fixes: dict[int, str] = {}
    file_path = BACKEND_ROOT / file_errors.file

    for attempt in range(max_attempts + 1):
        if not current_errors:
            # All errors fixed!
            break

        # Build prompt with current state
        current_file_errors = FileErrors(
            file=file_errors.file,
            errors=current_errors,
            content=current_content,
        )
        prompt = build_fix_prompt(current_file_errors)

        try:
            response = await call_kimi(client, api_key, prompt)
            fixes, skipped = parse_line_fixes(response)
        except Exception as e:
            return {
                "file": file_errors.file,
                "status": "error",
                "message": f"API error on attempt {attempt + 1}: {e}",
                "attempts": attempt + 1,
            }

        if not fixes:
            # No fixes generated, stop
            break

        # Validate indentation before applying
        valid_fixes = {
            line_num: code
            for line_num, code in fixes.items()
            if validate_indentation(current_content, code, line_num)
        }
        rejected = len(fixes) - len(valid_fixes)

        if not valid_fixes:
            # All fixes had bad indentation
            break

        # Apply valid fixes
        new_content = apply_line_fixes(current_content, valid_fixes)

        # Syntax check
        try:
            compile(new_content, file_errors.file, "exec")
        except SyntaxError as e:
            # Syntax error - revert and try again with remaining errors
            print(f"    ⚠ Attempt {attempt + 1}: syntax error, reverting")
            continue

        # Write temp file and check mypy
        if not dry_run:
            file_path.write_text(new_content)

        # Check if we reduced errors
        new_errors = run_mypy_on_file(file_errors.file)

        if len(new_errors) >= len(current_errors):
            # Made it worse or same - revert
            print(f"    ⚠ Attempt {attempt + 1}: {len(new_errors)} errors (was {len(current_errors)}), reverting")
            if not dry_run:
                file_path.write_text(current_content)
            continue

        # Success! Keep the changes
        current_content = new_content
        total_fixes += len(valid_fixes)
        all_fixes.update(valid_fixes)
        current_errors = new_errors

        # Update stats for fixed errors
        for err in file_errors.errors:
            if err.line in valid_fixes:
                update_error_stats(err.code, True)

        print(f"    ✓ Attempt {attempt + 1}: {len(current_errors)} errors remaining ({len(valid_fixes)} fixed, {rejected} rejected)")

    # Final state
    if not dry_run and current_content != original_content:
        file_path.write_text(current_content)

    # Update stats for unfixed errors
    for err in current_errors:
        update_error_stats(err.code, False)

    status = "success" if not current_errors else ("improved" if total_fixes > 0 else "failed")

    return {
        "file": file_errors.file,
        "status": status,
        "lines_fixed": total_fixes,
        "errors_before": len(file_errors.errors),
        "errors_after": len(current_errors),
        "attempts": attempt + 1,
        "fixes": all_fixes if dry_run else None,
    }


async def run_swarm(
    files: list[FileErrors],
    api_key: str,
    dry_run: bool = True,
    max_concurrent: int = MAX_CONCURRENT,
    repair_mode: bool = False,
    max_repair_attempts: int = MAX_REPAIR_ATTEMPTS,
) -> list[dict[str, Any]]:
    """Run the swarm of parallel fixes."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async with httpx.AsyncClient() as client:
        async def bounded_fix(file_errors: FileErrors) -> dict[str, Any]:
            async with semaphore:
                print(f"  Processing: {file_errors.file} ({len(file_errors.errors)} errors)")
                if repair_mode:
                    return await fix_file_with_repair(
                        client, api_key, file_errors, max_repair_attempts, dry_run
                    )
                else:
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
    parser.add_argument("--repair", action="store_true", help="Enable Generate-Check-Repair loop")
    parser.add_argument("--max-repair", type=int, default=MAX_REPAIR_ATTEMPTS, help="Max repair attempts per file")
    parser.add_argument("--swarm", action="store_true", help="Use swarm mode (batch files, trigger orchestrator)")
    parser.add_argument("--batch-size", type=int, default=10, help="Files per batch in swarm mode")
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

    # Run swarm or batch mode
    mode_parts = []
    if args.apply:
        mode_parts.append("APPLY")
    else:
        mode_parts.append("DRY RUN")
    if args.swarm:
        mode_parts.append(f"SWARM×{args.batch_size}")
    elif args.repair:
        mode_parts.append(f"REPAIR×{args.max_repair}")
    mode = " | ".join(mode_parts)
    print(f"\n[5/5] Running ({mode})...")

    if args.swarm:
        # Swarm mode: batch files together for orchestrator
        batch_results = []
        for i in range(0, len(file_errors_list), args.batch_size):
            batch = file_errors_list[i:i + args.batch_size]
            print(f"\n  Batch {i//args.batch_size + 1}: {len(batch)} files...")
            result = asyncio.run(run_swarm_batch(batch, api_key, dry_run=not args.apply))
            batch_results.append(result)

        # Flatten results for summary
        results = []
        for br in batch_results:
            if br.get("results"):
                results.extend(br["results"])
    else:
        results = asyncio.run(run_swarm(
            file_errors_list,
            api_key,
            dry_run=not args.apply,
            max_concurrent=args.concurrent,
            repair_mode=args.repair,
            max_repair_attempts=args.max_repair,
        ))

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    success_count = 0
    improved_count = 0
    total_errors_before = 0
    total_errors_after = 0

    for r in results:
        status = r.get("status", "unknown")
        file = r.get("file", "unknown")

        if args.swarm:
            # Swarm mode results
            fixes = r.get("fixes", 0)
            skips = r.get("skips", 0)
            errors = r.get("errors", 0)

            if status == "preview" or status == "applied":
                if fixes > 0:
                    success_count += 1
                    print(f"✓ {file}: {fixes}/{errors} errors fixed ({skips} skipped)")
                elif skips > 0:
                    print(f"⊘ {file}: {skips}/{errors} errors skipped")
                else:
                    print(f"? {file}: no response for {errors} errors")
            elif status == "syntax_error":
                print(f"✗ {file}: syntax error after fix attempt")
            elif status == "no_response":
                print(f"? {file}: {errors} errors - no fixes returned")
            else:
                print(f"✗ {file}: {r.get('message', status)}")
        elif args.repair:
            # Repair mode results
            errors_before = r.get("errors_before", 0)
            errors_after = r.get("errors_after", 0)
            attempts = r.get("attempts", 1)
            total_errors_before += errors_before
            total_errors_after += errors_after

            if status == "success":
                success_count += 1
                print(f"✓ {file}: {errors_before}→0 errors ({r['lines_fixed']} fixes, {attempts} attempts)")
            elif status == "improved":
                improved_count += 1
                print(f"◐ {file}: {errors_before}→{errors_after} errors ({r['lines_fixed']} fixes, {attempts} attempts)")
            elif status == "failed":
                print(f"✗ {file}: {errors_before} errors unchanged after {attempts} attempts")
            else:
                print(f"✗ {file}: {r.get('message', 'Unknown error')}")
        else:
            # Single-shot mode results
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

    # Summary stats
    if args.repair:
        print(f"\n📊 Results: {success_count} clean, {improved_count} improved, {len(results) - success_count - improved_count} unchanged")
        if total_errors_before > 0:
            reduction = total_errors_before - total_errors_after
            pct = 100 * reduction // total_errors_before
            print(f"📉 Errors: {total_errors_before} → {total_errors_after} ({reduction} fixed, {pct}% reduction)")
    else:
        print(f"\n📊 Success rate: {success_count}/{len(results)} ({100*success_count//len(results) if results else 0}%)")

    # Error type stats (if any)
    if ERROR_STATS:
        print("\n📈 Success by error type:")
        sorted_stats = sorted(ERROR_STATS.items(), key=lambda x: x[1]["success"], reverse=True)
        for code, stats in sorted_stats[:10]:  # Top 10
            total = stats["success"] + stats["fail"]
            rate = 100 * stats["success"] // total if total else 0
            print(f"  [{code}]: {rate}% ({stats['success']}/{total})")
        if len(sorted_stats) > 10:
            print(f"  ... and {len(sorted_stats) - 10} more error types")

    if not args.apply:
        print("\n⚠️  DRY RUN - No changes made. Use --apply to apply fixes.")
        print("   Review the results above, then run with --apply if satisfied.")


if __name__ == "__main__":
    main()
