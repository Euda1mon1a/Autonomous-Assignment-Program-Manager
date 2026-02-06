#!/usr/bin/env bash
# Codex operator safety audit:
# - HUMAN_TODO backlog visibility
# - pre-commit hook readiness
# - optional PII + gitleaks scans

set -euo pipefail

WITH_SCANS=false
TODO_ONLY=false
HOOKS_ONLY=false
SAVE=false

for arg in "$@"; do
  case "$arg" in
    --with-scans)
      WITH_SCANS=true
      ;;
    --todo-only)
      TODO_ONLY=true
      ;;
    --hooks-only)
      HOOKS_ONLY=true
      ;;
    --save)
      SAVE=true
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: $0 [--todo-only] [--hooks-only] [--with-scans] [--save]" >&2
      exit 2
      ;;
  esac
done

if [[ "$TODO_ONLY" == true && "$HOOKS_ONLY" == true ]]; then
  echo "Use either --todo-only or --hooks-only, not both." >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

timestamp="$(date '+%Y-%m-%d %H:%M:%S %Z')"
report_file="$(mktemp)"

append() {
  printf '%s\n' "$1" >>"$report_file"
}

append "# Codex Safety Audit"
append ""
append "- Timestamp: \`$timestamp\`"
append "- Repo: \`$REPO_ROOT\`"
append ""

run_todo_section() {
  append "## TODO Audit"
  append ""

  if [[ ! -f "HUMAN_TODO.md" ]]; then
    append "- Status: \`HUMAN_TODO.md not found\`"
    append ""
    return
  fi

  open_count="$(rg -n "^- \\[ \\]" HUMAN_TODO.md | wc -l | tr -d ' ')"
  high_open_count="$(
    awk '
      /^## / {
        if (seen && priority ~ /High/ && open) count++
        seen=1; priority=""; open=0
      }
      /\*\*Priority:\*\*/ { priority=$0 }
      /^- \[ \]/ { open=1 }
      END {
        if (seen && priority ~ /High/ && open) count++
        print count+0
      }
    ' HUMAN_TODO.md
  )"

  append "- Open checklist items: \`$open_count\`"
  append "- High-priority sections with open items: \`$high_open_count\`"
  append ""
  append "### Top Open Items"
  append ""
  append '```text'
  rg -n "^- \\[ \\]" HUMAN_TODO.md | head -n 10 >>"$report_file" || true
  append '```'
  append ""
}

run_hooks_section() {
  append "## Hook Audit"
  append ""

  if command -v pre-commit >/dev/null 2>&1; then
    precommit_version="$(pre-commit --version 2>/dev/null || echo 'unknown')"
    append "- pre-commit: \`$precommit_version\`"
  else
    append "- pre-commit: \`missing\`"
    append ""
    append "**Result:** FAIL (pre-commit not installed)"
    append ""
    return 1
  fi

  hooks_path="$(git config --get core.hooksPath || echo '.git/hooks')"
  append "- git hooks path: \`$hooks_path\`"

  if [[ -f ".git/hooks/pre-commit" ]]; then
    append "- .git/hooks/pre-commit: \`present\`"
  else
    append "- .git/hooks/pre-commit: \`missing\`"
  fi

  append ""

  pii_status="not_run"
  gitleaks_status="not_run"
  scan_failed=0

  if [[ "$WITH_SCANS" == true ]]; then
    set +e
    pii_output="$(pre-commit run pii-scan --all-files 2>&1)"
    pii_rc=$?
    set -e
    if [[ $pii_rc -eq 0 ]]; then
      pii_status="pass"
    else
      pii_status="fail"
      scan_failed=1
    fi

    set +e
    gitleaks_output="$(pre-commit run gitleaks --all-files 2>&1)"
    gitleaks_rc=$?
    set -e
    if [[ $gitleaks_rc -eq 0 ]]; then
      gitleaks_status="pass"
    else
      gitleaks_status="fail"
      scan_failed=1
    fi

    append "### Security Scan Results"
    append ""
    append "- pii-scan: \`$pii_status\`"
    append "- gitleaks: \`$gitleaks_status\`"
    append ""
    append "### pii-scan Output (tail)"
    append ""
    append '```text'
    printf '%s\n' "$pii_output" | tail -n 20 >>"$report_file"
    append '```'
    append ""
    append "### gitleaks Output (tail)"
    append ""
    append '```text'
    printf '%s\n' "$gitleaks_output" | tail -n 20 >>"$report_file"
    append '```'
    append ""
  fi

  if [[ "$WITH_SCANS" == true && $scan_failed -ne 0 ]]; then
    append "**Result:** FAIL (one or more security scans failed)"
    append ""
    return 1
  fi

  append "**Result:** PASS"
  append ""
}

overall_rc=0

if [[ "$HOOKS_ONLY" == true ]]; then
  run_hooks_section || overall_rc=1
elif [[ "$TODO_ONLY" == true ]]; then
  run_todo_section
else
  run_todo_section
  run_hooks_section || overall_rc=1
fi

cat "$report_file"

if [[ "$SAVE" == true ]]; then
  mkdir -p docs/reports/automation
  out="docs/reports/automation/codex_safety_audit_$(date '+%Y%m%d-%H%M').md"
  cp "$report_file" "$out"
  echo ""
  echo "Saved report: $out"
fi

rm -f "$report_file"
exit $overall_rc
