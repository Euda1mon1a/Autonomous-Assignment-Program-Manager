#!/usr/bin/env bash
# Build a safe Codex worktree prune plan.
#
# Safety rules:
# - default excludes `bad1`
# - only marks worktrees as prune-ready when clean + zero unique commits vs base ref
# - no deletion unless --apply is explicitly provided
#
# Usage:
#   .codex/scripts/codex_safe_prune_plan.sh --save
#   .codex/scripts/codex_safe_prune_plan.sh --exclude-ids bad1,foo --save
#   .codex/scripts/codex_safe_prune_plan.sh --apply --exclude-ids bad1

set -euo pipefail

WORKTREE_ROOT="${HOME}/.codex/worktrees"
REPO_NAME="Autonomous-Assignment-Program-Manager"
BASE_REF="origin/main"
EXCLUDE_IDS="bad1"
SAVE=false
OUTPUT=""
APPLY=false

usage() {
  cat <<'EOF'
Usage:
  .codex/scripts/codex_safe_prune_plan.sh [options]

Options:
  --worktree-root PATH   Root directory for Codex worktrees (default: ~/.codex/worktrees)
  --repo-name NAME       Repo dir name in each worktree (default: Autonomous-Assignment-Program-Manager)
  --base-ref REF         Ref for uniqueness checks (default: origin/main)
  --exclude-ids CSV      Worktree IDs to keep regardless of status (default: bad1)
  --save                 Save report to docs/reports/automation/
  --output PATH          Explicit report output path
  --apply                Execute prune for prune-ready worktrees only
  -h, --help             Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --worktree-root)
      WORKTREE_ROOT="${2:-}"
      shift 2
      ;;
    --repo-name)
      REPO_NAME="${2:-}"
      shift 2
      ;;
    --base-ref)
      BASE_REF="${2:-}"
      shift 2
      ;;
    --exclude-ids)
      EXCLUDE_IDS="${2:-}"
      shift 2
      ;;
    --save)
      SAVE=true
      shift
      ;;
    --output)
      OUTPUT="${2:-}"
      shift 2
      ;;
    --apply)
      APPLY=true
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

if [[ ! -d "${WORKTREE_ROOT}" ]]; then
  echo "Worktree root not found: ${WORKTREE_ROOT}" >&2
  exit 1
fi

is_excluded() {
  local id="$1"
  local list=",${EXCLUDE_IDS},"
  [[ "${list}" == *",${id},"* ]]
}

REPOS="$(find "${WORKTREE_ROOT}" -mindepth 2 -maxdepth 2 -type d -name "${REPO_NAME}" 2>/dev/null | sort || true)"

if [[ -z "${REPOS}" ]]; then
  echo "No worktree repos found under ${WORKTREE_ROOT} for ${REPO_NAME}."
  exit 0
fi

report=""
report+="# Codex Safe Prune Plan"$'\n'
report+=$'\n'
report+="- Timestamp: \`$(date '+%Y-%m-%d %H:%M:%S %Z')\`"$'\n'
report+="- Worktree root: \`${WORKTREE_ROOT}\`"$'\n'
report+="- Base ref: \`${BASE_REF}\`"$'\n'
report+="- Excluded IDs: \`${EXCLUDE_IDS}\`"$'\n'
report+="- Mode: \`$([[ "${APPLY}" == true ]] && echo apply || echo plan-only)\`"$'\n'
report+=$'\n'

report+="## BLUF"$'\n'
report+=$'\n'

table="| ID | Dirty | Unique | Decision | Reason |"$'\n'
table+="|---|---:|---:|---|---|"$'\n'

safe_ids=()
pruned_ids=()
blocked_ids=()
excluded_ids=()

while IFS= read -r repo; do
  [[ -n "${repo}" ]] || continue
  wt_dir="$(dirname "${repo}")"
  wt_id="$(basename "${wt_dir}")"

  dirty_lines="$(git -C "${repo}" status --porcelain 2>/dev/null || true)"
  if [[ -n "${dirty_lines}" ]]; then
    dirty_count="$(printf '%s\n' "${dirty_lines}" | sed '/^$/d' | wc -l | tr -d ' ')"
  else
    dirty_count=0
  fi

  if git -C "${repo}" rev-parse --verify "${BASE_REF}" >/dev/null 2>&1; then
    unique_lines="$(git -C "${repo}" cherry -v "${BASE_REF}" HEAD 2>/dev/null | rg '^\+' || true)"
    if [[ -n "${unique_lines}" ]]; then
      unique_count="$(printf '%s\n' "${unique_lines}" | sed '/^$/d' | wc -l | tr -d ' ')"
    else
      unique_count=0
    fi
  else
    unique_count=0
  fi

  decision="keep"
  reason="review"
  if is_excluded "${wt_id}"; then
    decision="keep"
    reason="explicitly excluded"
    excluded_ids+=("${wt_id}")
  elif (( dirty_count > 0 )); then
    decision="keep"
    reason="dirty worktree"
    blocked_ids+=("${wt_id}")
  elif (( unique_count > 0 )); then
    decision="keep"
    reason="unique commits"
    blocked_ids+=("${wt_id}")
  else
    decision="prune-ready"
    reason="clean + no unique commits"
    safe_ids+=("${wt_id}")
  fi

  if [[ "${APPLY}" == true && "${decision}" == "prune-ready" ]]; then
    rm -rf "${wt_dir}"
    decision="pruned"
    reason="pruned by apply mode"
    pruned_ids+=("${wt_id}")
  fi

  table+="| \`${wt_id}\` | ${dirty_count} | ${unique_count} | \`${decision}\` | ${reason} |"$'\n'
done <<< "${REPOS}"

report+="- Worktrees scanned: \`$(printf '%s\n' "${REPOS}" | sed '/^$/d' | wc -l | tr -d ' ')\`"$'\n'
report+="- Prune-ready now: \`${#safe_ids[@]}\`"$'\n'
report+="- Excluded by policy: \`${#excluded_ids[@]}\`"$'\n'
report+="- Blocked (dirty/unique): \`${#blocked_ids[@]}\`"$'\n'
if [[ "${APPLY}" == true ]]; then
  report+="- Pruned in this run: \`${#pruned_ids[@]}\`"$'\n'
fi
report+=$'\n'

if (( ${#safe_ids[@]} > 0 )); then
  report+="Safe prune set: \`$(IFS=,; echo "${safe_ids[*]}")\`"$'\n'
else
  report+="Safe prune set: \`none\`"$'\n'
fi
report+=$'\n'

report+="## Plan Table"$'\n'
report+=$'\n'
report+="${table}"$'\n'

report+="## Manual Command (Plan Mode)"$'\n'
report+=$'\n'
if (( ${#safe_ids[@]} > 0 )); then
  report+='```bash'$'\n'
  for id in "${safe_ids[@]}"; do
    report+="rm -rf \"${WORKTREE_ROOT}/${id}\""$'\n'
  done
  report+='```'$'\n'
else
  report+="- No prune-ready worktrees."$'\n'
fi
report+=$'\n'

report+="## Notes"$'\n'
report+=$'\n'
report+="- This plan intentionally excludes \`bad1\` unless you remove it from \`--exclude-ids\`."$'\n'
report+="- Re-run this script before any destructive cleanup to account for new commits."$'\n'

if [[ "${SAVE}" == true || -n "${OUTPUT}" ]]; then
  out="${OUTPUT}"
  if [[ -z "${out}" ]]; then
    out="docs/reports/automation/codex_safe_prune_plan_$(date '+%Y%m%d-%H%M').md"
  fi
  mkdir -p "$(dirname "${out}")"
  printf '%s\n' "${report}" > "${out}"
  echo "${out}"
else
  printf '%s\n' "${report}"
fi
