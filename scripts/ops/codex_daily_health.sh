#!/usr/bin/env bash
# Unified Codex daily health check:
# - MCP visibility and local MCP health
# - hook + PII scanner readiness
# - cherry-pick risk visibility
# - skill drift visibility
# - automation schedule snapshot
#
# Usage:
#   scripts/ops/codex_daily_health.sh
#   scripts/ops/codex_daily_health.sh --save

set -euo pipefail

SAVE=false
OUTPUT=""
INCLUDE_STORAGE=false
SKIP_SCANS=false

usage() {
  cat <<'EOF'
Usage:
  scripts/ops/codex_daily_health.sh [options]

Options:
  --save            Save markdown report to docs/reports/automation/
  --output PATH     Explicit output path
  --with-storage    Include storage audit snippet
  --skip-scans      Skip pii-scan/gitleaks in hook audit
  -h, --help        Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --save)
      SAVE=true
      shift
      ;;
    --output)
      OUTPUT="${2:-}"
      shift 2
      ;;
    --with-storage)
      INCLUDE_STORAGE=true
      shift
      ;;
    --skip-scans)
      SKIP_SCANS=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "${REPO_ROOT}"

report_file="$(mktemp)"
trap 'rm -f "${report_file}"' EXIT

overall_rc=0

append() {
  printf '%s\n' "$1" >>"${report_file}"
}

append "# Codex Daily Health"
append ""
append "- Timestamp: \`$(date '+%Y-%m-%d %H:%M:%S %Z')\`"
append "- Repo: \`${REPO_ROOT}\`"
append ""

if [[ -f ".codex/setup.sh" ]]; then
  # shellcheck disable=SC1091
  source ".codex/setup.sh"
fi

append "## MCP Visibility"
append ""
set +e
if [[ -f ".codex/config.toml" ]]; then
  mcp_config_source=".codex/config.toml"
  mcp_list_output="$(CODEX_HOME=.codex codex mcp list 2>&1)"
  mcp_list_rc=$?
else
  mcp_config_source="default (~/.codex/config.toml)"
  mcp_list_output="$(codex mcp list 2>&1)"
  mcp_list_rc=$?
fi
set -e
if [[ ${mcp_list_rc} -eq 0 ]]; then
  enabled_count="$(printf '%s\n' "${mcp_list_output}" | rg -n "enabled" | wc -l | tr -d ' ' || true)"
  enabled_count="${enabled_count:-0}"
  append "- codex mcp list: \`ok\`"
  append "- codex mcp config source: \`${mcp_config_source}\`"
  append "- enabled rows detected: \`${enabled_count}\`"
else
  append "- codex mcp list: \`fail\` (exit ${mcp_list_rc})"
  append "- codex mcp config source: \`${mcp_config_source}\`"
  overall_rc=1
fi
append ""
append '```text'
append "${mcp_list_output}"
append '```'
append ""

append "## Local MCP Server"
append ""
set +e
mcp_health_json="$(curl -sSf http://127.0.0.1:8081/health 2>/dev/null)"
mcp_health_rc=$?
set -e
if [[ ${mcp_health_rc} -eq 0 ]]; then
  service_status="$(printf '%s\n' "${mcp_health_json}" | rg -o '"status":"[^"]+"' | head -n1 | cut -d':' -f2 | tr -d '"' || true)"
  api_creds="$(printf '%s\n' "${mcp_health_json}" | rg -o '"api_credentials_configured":[^,}]+' | cut -d':' -f2 || true)"
  append "- health endpoint: \`ok\`"
  append "- status: \`${service_status:-unknown}\`"
  append "- api_credentials_configured: \`${api_creds:-unknown}\`"
  if [[ "${service_status}" != "healthy" ]]; then
    overall_rc=1
  fi
else
  append "- health endpoint: \`fail\` (http://127.0.0.1:8081/health)"
  overall_rc=1
fi
append ""
append '```json'
append "${mcp_health_json:-"{}"}"
append '```'
append ""

append "## Hook + Scanner Health"
append ""
hook_args=(--hooks-only --save)
if [[ "${SKIP_SCANS}" == false ]]; then
  hook_args=(--hooks-only --with-scans --save)
fi
set +e
hook_output="$(scripts/ops/codex_safety_audit.sh "${hook_args[@]}" 2>&1)"
hook_rc=$?
set -e
if [[ ${hook_rc} -eq 0 ]]; then
  append "- codex_safety_audit: \`pass\`"
else
  append "- codex_safety_audit: \`fail\` (exit ${hook_rc})"
  overall_rc=1
fi
hook_report_path="$(printf '%s\n' "${hook_output}" | rg -o 'docs/reports/automation/[^[:space:]]+' | tail -n1 || true)"
if [[ -n "${hook_report_path}" ]]; then
  append "- report: \`${hook_report_path}\`"
fi
append ""
append '```text'
append "${hook_output}"
append '```'
append ""

append "## Cherry-Pick Risk"
append ""
set +e
hunter_output="$(scripts/ops/codex_cherry_pick_hunter.sh --save 2>&1)"
hunter_rc=$?
set -e
hunter_report_path="$(printf '%s\n' "${hunter_output}" | tail -n1)"
if [[ ${hunter_rc} -eq 0 ]]; then
  append "- hunter report: \`${hunter_report_path}\`"
else
  append "- hunter run failed: \`exit ${hunter_rc}\`"
  overall_rc=1
fi
set +e
scripts/ops/codex_cherry_pick_hunter.sh --risk-check >/dev/null 2>&1
risk_rc=$?
set -e
if [[ ${risk_rc} -eq 0 ]]; then
  append "- risk status: \`clear\`"
elif [[ ${risk_rc} -eq 3 ]]; then
  append "- risk status: \`attention required\`"
  overall_rc=1
else
  append "- risk status: \`unknown (exit ${risk_rc})\`"
  overall_rc=1
fi
append ""

append "## Skill Drift"
append ""
set +e
skill_output="$(scripts/ops/codex_skill_audit.sh --save 2>&1)"
skill_rc=$?
set -e
if [[ ${skill_rc} -eq 0 ]]; then
  skill_report_path="$(printf '%s\n' "${skill_output}" | tail -n1)"
  append "- codex_skill_audit: \`ok\`"
  append "- report: \`${skill_report_path}\`"
else
  append "- codex_skill_audit: \`fail\` (exit ${skill_rc})"
  overall_rc=1
fi
append ""

append "## Automation Schedule Snapshot"
append ""
set +e
schedule_output="$(scripts/ops/codex_app_schedule_status.sh 2>&1)"
schedule_rc=$?
set -e
if [[ ${schedule_rc} -eq 0 ]]; then
  append "- codex_app_schedule_status: \`ok\`"
else
  append "- codex_app_schedule_status: \`fail\` (exit ${schedule_rc})"
  overall_rc=1
fi
append ""
append '```text'
append "${schedule_output}"
append '```'
append ""

if [[ "${INCLUDE_STORAGE}" == true ]]; then
  append "## Storage Snapshot"
  append ""
  set +e
  storage_output="$(scripts/ops/codex_storage_hygiene.sh --audit 2>&1)"
  storage_rc=$?
  set -e
  if [[ ${storage_rc} -eq 0 ]]; then
    append "- codex_storage_hygiene --audit: \`ok\`"
  else
    append "- codex_storage_hygiene --audit: \`fail\` (exit ${storage_rc})"
    overall_rc=1
  fi
  append ""
  append '```text'
  append "$(printf '%s\n' "${storage_output}" | sed -n '1,80p')"
  append '```'
  append ""
fi

append "## Overall"
append ""
if [[ ${overall_rc} -eq 0 ]]; then
  append "**Result:** PASS"
else
  append "**Result:** ATTENTION REQUIRED"
fi

cat "${report_file}"

if [[ "${SAVE}" == true || -n "${OUTPUT}" ]]; then
  out="${OUTPUT}"
  if [[ -z "${out}" ]]; then
    out="docs/reports/automation/codex_daily_health_$(date '+%Y%m%d-%H%M').md"
  fi
  mkdir -p "$(dirname "${out}")"
  cp "${report_file}" "${out}"
  echo ""
  echo "Saved report: ${out}"
fi

exit "${overall_rc}"
