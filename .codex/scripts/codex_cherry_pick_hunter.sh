#!/usr/bin/env bash
# Find Codex worktree commits worth cherry-picking before cleanup/deletion.

set -euo pipefail

WORKTREE_ROOT="${HOME}/.codex/worktrees"
REPO_NAME="Autonomous-Assignment-Program-Manager"
BASE_REF="origin/main"
MAX_COMMITS=20
SAVE=false
OUTPUT=""
RISK_CHECK=false
PRESERVE_HEADS=false
PRESERVE_PREFIX="codex/salvage"

usage() {
  cat <<'EOF'
Usage:
  scripts/ops/codex_cherry_pick_hunter.sh [options]

Options:
  --worktree-root PATH   Worktree root (default: ~/.codex/worktrees)
  --repo-name NAME       Repo folder in each worktree (default: Autonomous-Assignment-Program-Manager)
  --base-ref REF         Compare against ref (default: origin/main)
  --max-commits N        Max listed unique commits per worktree (default: 20)
  --save                 Save markdown report to docs/reports/automation/
  --output PATH          Explicit output path for report
  --risk-check           Quiet mode for safety gates. Exit 0 if no findings, 3 if findings.
  --preserve-heads       Create local salvage branches for risky worktree heads.
  --preserve-prefix PFX  Branch prefix for preserved heads (default: codex/salvage)
  -h, --help             Show help

Findings:
  - Unique commits: patch-unique commits from `git cherry -v <base> HEAD`
  - Dirty state: uncommitted files in worktree repo
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --worktree-root)
      WORKTREE_ROOT="$2"
      shift 2
      ;;
    --repo-name)
      REPO_NAME="$2"
      shift 2
      ;;
    --base-ref)
      BASE_REF="$2"
      shift 2
      ;;
    --max-commits)
      MAX_COMMITS="$2"
      shift 2
      ;;
    --save)
      SAVE=true
      shift
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --risk-check)
      RISK_CHECK=true
      shift
      ;;
    --preserve-heads)
      PRESERVE_HEADS=true
      shift
      ;;
    --preserve-prefix)
      PRESERVE_PREFIX="$2"
      shift 2
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

if [[ ! "${MAX_COMMITS}" =~ ^[0-9]+$ ]]; then
  echo "--max-commits must be a non-negative integer (got: ${MAX_COMMITS})" >&2
  exit 2
fi

REPOS="$(find "${WORKTREE_ROOT}" -mindepth 2 -maxdepth 2 -type d -name "${REPO_NAME}" 2>/dev/null | sort || true)"

if [[ -z "${REPOS}" ]]; then
  if [[ "${RISK_CHECK}" == true ]]; then
    exit 0
  fi
  echo "No worktree repos found under ${WORKTREE_ROOT} for ${REPO_NAME}."
  exit 0
fi

total_worktrees=0
worktrees_with_unique=0
worktrees_dirty=0
total_unique_commits=0
preserved_branches=0
preserve_notes=""

report=""
report+="# Codex Cherry-Pick Hunter"$'\n'
report+=$'\n'
report+="- Worktree root: \`${WORKTREE_ROOT}\`"$'\n'
report+="- Repo name: \`${REPO_NAME}\`"$'\n'
report+="- Base ref: \`${BASE_REF}\`"$'\n'
report+=$'\n'
report+="## Summary"$'\n'
report+=$'\n'
report+="| Worktree | HEAD | Dirty | Unique | Status |"$'\n'
report+="|---|---|---:|---:|---|"$'\n'

details=""

while IFS= read -r repo; do
  [[ -n "${repo}" ]] || continue
  if ! git -C "${repo}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    continue
  fi
  total_worktrees=$(( total_worktrees + 1 ))

  wt_id="$(basename "$(dirname "${repo}")")"
  head_short="$(git -C "${repo}" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
  head_subject="$(git -C "${repo}" log -1 --pretty=format:%s 2>/dev/null || echo "unknown")"

  dirty_lines="$(git -C "${repo}" status --porcelain 2>/dev/null || true)"
  if [[ -n "${dirty_lines}" ]]; then
    dirty_count="$(printf '%s\n' "${dirty_lines}" | sed '/^$/d' | wc -l | tr -d ' ')"
  else
    dirty_count=0
  fi

  if git -C "${repo}" rev-parse --verify "${BASE_REF}" >/dev/null 2>&1; then
    cherry_lines="$(git -C "${repo}" cherry -v "${BASE_REF}" HEAD 2>/dev/null || true)"
    unique_lines="$(printf '%s\n' "${cherry_lines}" | rg '^\+' || true)"
    if [[ -n "${unique_lines}" ]]; then
      unique_count="$(printf '%s\n' "${unique_lines}" | sed '/^$/d' | wc -l | tr -d ' ')"
    else
      unique_count=0
    fi
  else
    unique_lines=""
    unique_count=0
  fi

  if (( unique_count > 0 )); then
    worktrees_with_unique=$(( worktrees_with_unique + 1 ))
    total_unique_commits=$(( total_unique_commits + unique_count ))
  fi
  if (( dirty_count > 0 )); then
    worktrees_dirty=$(( worktrees_dirty + 1 ))
  fi

  status="safe"
  if (( unique_count > 0 && dirty_count > 0 )); then
    status="review+dirty"
  elif (( unique_count > 0 )); then
    status="review"
  elif (( dirty_count > 0 )); then
    status="dirty"
  fi

  report+="| \`${wt_id}\` | \`${head_short}\` ${head_subject} | ${dirty_count} | ${unique_count} | \`${status}\` |"$'\n'

  if [[ "${PRESERVE_HEADS}" == true && ( ${unique_count} -gt 0 || ${dirty_count} -gt 0 ) ]]; then
    stamp="$(date '+%Y%m%d')"
    preserve_branch="${PRESERVE_PREFIX}/${wt_id}-${head_short}-${stamp}"
    if git -C "${repo}" show-ref --verify --quiet "refs/heads/${preserve_branch}"; then
      preserve_notes+="- ${wt_id}: already preserved at \`${preserve_branch}\`"$'\n'
    else
      git -C "${repo}" branch "${preserve_branch}" "${head_short}"
      preserved_branches=$(( preserved_branches + 1 ))
      preserve_notes+="- ${wt_id}: preserved at \`${preserve_branch}\` -> \`${head_short}\`"$'\n'
    fi
  fi

  details+="### ${wt_id}"$'\n'
  details+="- Path: \`${repo}\`"$'\n'
  details+="- HEAD: \`${head_short}\` ${head_subject}"$'\n'
  details+="- Dirty files: ${dirty_count}"$'\n'
  details+="- Unique commits vs \`${BASE_REF}\`: ${unique_count}"$'\n'
  if (( unique_count > 0 )); then
    details+=$'\n'"Unique commits:"$'\n'
    details+='```text'$'\n'
    details+="$(printf '%s\n' "${unique_lines}" | head -n "${MAX_COMMITS}")"$'\n'
    details+='```'$'\n'
    details+=$'\n'"Cherry-pick commands:"$'\n'
    details+='```bash'$'\n'
    while IFS= read -r line; do
      [[ -n "${line}" ]] || continue
      sha="$(printf '%s\n' "${line}" | awk '{print $2}')"
      [[ -n "${sha}" ]] || continue
      details+="git cherry-pick ${sha}"$'\n'
    done < <(printf '%s\n' "${unique_lines}" | head -n "${MAX_COMMITS}")
    details+='```'$'\n'
  fi
  if (( dirty_count > 0 )); then
    details+=$'\n'"Dirty paths:"$'\n'
    details+='```text'$'\n'
    details+="$(printf '%s\n' "${dirty_lines}" | head -n 40)"$'\n'
    details+='```'$'\n'
  fi
  details+=$'\n'
done <<< "${REPOS}"

report+=$'\n'
report+="- Worktrees scanned: ${total_worktrees}"$'\n'
report+="- Worktrees with unique commits: ${worktrees_with_unique}"$'\n'
report+="- Total unique commits: ${total_unique_commits}"$'\n'
report+="- Worktrees with dirty state: ${worktrees_dirty}"$'\n'
report+="- Preserved branches created: ${preserved_branches}"$'\n'
if [[ -n "${preserve_notes}" ]]; then
  report+=$'\n'"### Preservation"$'\n'
  report+=$'\n'"${preserve_notes}"
fi
report+=$'\n'
report+="## Details"$'\n'
report+=$'\n'
report+="${details}"

findings=0
if (( worktrees_with_unique > 0 || worktrees_dirty > 0 )); then
  findings=1
fi

if [[ "${RISK_CHECK}" == true ]]; then
  if (( findings == 1 )); then
    exit 3
  fi
  exit 0
fi

if [[ "${SAVE}" == true || -n "${OUTPUT}" ]]; then
  out="${OUTPUT}"
  if [[ -z "${out}" ]]; then
    out="docs/reports/automation/codex_cherry_pick_hunter_$(date '+%Y%m%d-%H%M').md"
  fi
  mkdir -p "$(dirname "${out}")"
  printf '%s\n' "${report}" > "${out}"
  echo "${out}"
else
  printf '%s\n' "${report}"
fi
