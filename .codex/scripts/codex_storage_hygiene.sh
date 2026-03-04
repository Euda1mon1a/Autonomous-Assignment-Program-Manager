#!/usr/bin/env bash
# Codex App storage hygiene for macOS/local dev machines.
# Default behavior is read-only audit. Destructive actions require --apply.

set -euo pipefail

CODEX_ROOT="${CODEX_HOME:-$HOME/.codex}"
WORKTREE_ROOT="${CODEX_ROOT}/worktrees"
DEFAULT_REPO_NAME="Autonomous-Assignment-Program-Manager"
STALE_DAYS=7
SESSION_DAYS=30
BASE_REF="origin/main"
ALLOW_RISKY_PRUNE=false

DO_AUDIT=true
DO_CACHE_CLEAN=false
DO_LIST_STALE=false
DO_PRUNE_STALE=false
DO_LIST_OLD_SESSIONS=false
DO_PRUNE_OLD_SESSIONS=false
APPLY=false
REPO_NAME="${DEFAULT_REPO_NAME}"

usage() {
  cat <<'EOF'
Usage:
  scripts/ops/codex_storage_hygiene.sh [options]

Options:
  --audit                Run storage audit (default).
  --clean-caches         Find common cache directories in ~/.codex/worktrees.
                         With --apply, delete them.
  --list-stale           List stale clean worktrees older than --days.
  --prune-stale          Delete stale clean worktrees older than --days.
                         Requires --apply.
  --list-old-sessions    List Codex session/archived_session files older than --session-days.
  --prune-old-sessions   Delete Codex session/archived_session files older than --session-days.
                         Requires --apply.
  --days N               Staleness threshold in days (default: 7).
  --session-days N       Session retention threshold in days (default: 30).
  --base-ref REF         Base ref for cherry-pick hunter safety gate (default: origin/main).
  --allow-risky-prune    Bypass cherry-pick hunter gate during --prune-stale.
  --repo-name NAME       Repo folder name under each worktree
                         (default: Autonomous-Assignment-Program-Manager).
  --apply                Execute deletions. Without this, all delete modes are dry-run.
  -h, --help             Show help.

Examples:
  scripts/ops/codex_storage_hygiene.sh --audit
  scripts/ops/codex_storage_hygiene.sh --clean-caches
  scripts/ops/codex_storage_hygiene.sh --clean-caches --apply
  scripts/ops/codex_storage_hygiene.sh --list-stale --days 14
  scripts/ops/codex_storage_hygiene.sh --prune-stale --days 14 --apply
  scripts/ops/codex_storage_hygiene.sh --list-old-sessions --session-days 45
  scripts/ops/codex_storage_hygiene.sh --prune-old-sessions --session-days 45 --apply
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --audit)
      DO_AUDIT=true
      shift
      ;;
    --clean-caches)
      DO_CACHE_CLEAN=true
      DO_AUDIT=false
      shift
      ;;
    --list-stale)
      DO_LIST_STALE=true
      DO_AUDIT=false
      shift
      ;;
    --prune-stale)
      DO_PRUNE_STALE=true
      DO_AUDIT=false
      shift
      ;;
    --list-old-sessions)
      DO_LIST_OLD_SESSIONS=true
      DO_AUDIT=false
      shift
      ;;
    --prune-old-sessions)
      DO_PRUNE_OLD_SESSIONS=true
      DO_AUDIT=false
      shift
      ;;
    --days)
      STALE_DAYS="${2:-}"
      shift 2
      ;;
    --base-ref)
      BASE_REF="${2:-}"
      shift 2
      ;;
    --session-days)
      SESSION_DAYS="${2:-}"
      shift 2
      ;;
    --allow-risky-prune)
      ALLOW_RISKY_PRUNE=true
      shift
      ;;
    --repo-name)
      REPO_NAME="${2:-}"
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

if [[ ! -d "${CODEX_ROOT}" ]]; then
  echo "Codex root not found: ${CODEX_ROOT}" >&2
  exit 1
fi

if [[ ! "${STALE_DAYS}" =~ ^[0-9]+$ ]]; then
  echo "--days must be a non-negative integer (got: ${STALE_DAYS})" >&2
  exit 2
fi

if [[ ! "${SESSION_DAYS}" =~ ^[0-9]+$ ]]; then
  echo "--session-days must be a non-negative integer (got: ${SESSION_DAYS})" >&2
  exit 2
fi

if [[ "${DO_PRUNE_STALE}" == true && "${APPLY}" == false ]]; then
  echo "Refusing prune without --apply. Use --list-stale for dry-run listing." >&2
  exit 2
fi

if [[ "${DO_PRUNE_OLD_SESSIONS}" == true && "${APPLY}" == false ]]; then
  echo "Refusing session prune without --apply. Use --list-old-sessions for dry-run listing." >&2
  exit 2
fi

human_size() {
  # Input: kilobytes
  local kb="${1:-0}"
  awk -v kib="${kb}" '
    BEGIN {
      split("KB MB GB TB", u, " ");
      i=1; s=kib+0;
      while (s >= 1024 && i < 4) { s/=1024; i++; }
      if (i == 1) printf "%.0f %s", s, u[i];
      else printf "%.1f %s", s, u[i];
    }
  '
}

epoch_mtime() {
  local path="$1"
  stat -f "%m" "$path"
}

days_old() {
  local path="$1"
  local now
  now="$(date +%s)"
  local mt
  mt="$(epoch_mtime "$path")"
  echo $(( (now - mt) / 86400 ))
}

worktree_repo_paths() {
  find "${WORKTREE_ROOT}" -mindepth 2 -maxdepth 2 -type d -name "${REPO_NAME}" 2>/dev/null | sort
}

cache_candidates() {
  local rel
  while IFS= read -r repo; do
    [[ -n "${repo}" ]] || continue
    for rel in \
      "frontend/node_modules" \
      "frontend/.next" \
      "frontend/.npm-cache" \
      "backend/.mypy_cache" \
      "backend/.pytest_cache" \
      "backend/.ruff_cache" \
      "backend/.hypothesis"; do
      local d="${repo}/${rel}"
      [[ -d "${d}" ]] && echo "${d}"
    done
  done < <(worktree_repo_paths)
}

audit() {
  echo "# Codex Storage Audit"
  echo ""
  echo "- CodeX root: ${CODEX_ROOT}"
  echo "- Worktree root: ${WORKTREE_ROOT}"
  echo ""
  echo "## Top Directories"
  du -h -d 2 "${CODEX_ROOT}" 2>/dev/null | sort -hr | sed -n '1,20p'
  echo ""

  local total_cache_kb=0
  local count=0
  while IFS= read -r d; do
    [[ -n "${d}" ]] || continue
    local kb
    kb="$(du -sk "${d}" 2>/dev/null | awk '{print $1}')"
    kb="${kb:-0}"
    total_cache_kb=$(( total_cache_kb + kb ))
    count=$(( count + 1 ))
  done < <(cache_candidates)

  echo "## Cache Pressure"
  echo "- Cache directories in worktrees: ${count}"
  echo "- Estimated removable cache size: $(human_size "${total_cache_kb}")"
  echo ""

  echo "## Large Worktrees"
  for wt in "${WORKTREE_ROOT}"/*; do
    [[ -d "${wt}" ]] || continue
    local size
    size="$(du -sh "${wt}" 2>/dev/null | awk '{print $1}')"
    echo "- $(basename "${wt}"): ${size}"
  done | sort -t: -k2,2hr
  echo ""
  echo "Run next:"
  echo "- scripts/ops/codex_storage_hygiene.sh --clean-caches"
  echo "- scripts/ops/codex_storage_hygiene.sh --list-stale --days ${STALE_DAYS}"
}

clean_caches() {
  echo "# Codex Cache Cleanup"
  echo ""
  echo "- Mode: $([[ "${APPLY}" == true ]] && echo "apply" || echo "dry-run")"
  echo ""

  local total_kb=0
  local deleted_kb=0
  local count=0
  local deleted_count=0

  while IFS= read -r d; do
    [[ -n "${d}" ]] || continue
    local kb
    kb="$(du -sk "${d}" 2>/dev/null | awk '{print $1}')"
    kb="${kb:-0}"
    total_kb=$(( total_kb + kb ))
    count=$(( count + 1 ))
    echo "- ${d} ($(human_size "${kb}"))"

    if [[ "${APPLY}" == true ]]; then
      rm -rf "${d}"
      deleted_kb=$(( deleted_kb + kb ))
      deleted_count=$(( deleted_count + 1 ))
    fi
  done < <(cache_candidates | sort -u)

  echo ""
  if [[ "${APPLY}" == true ]]; then
    echo "Deleted cache dirs: ${deleted_count}/${count}"
    echo "Freed: $(human_size "${deleted_kb}")"
  else
    echo "Would delete cache dirs: ${count}"
    echo "Would free: $(human_size "${total_kb}")"
    echo "Re-run with --apply to execute."
  fi
}

list_or_prune_stale() {
  local mode="$1" # list|prune
  echo "# Codex Stale Worktrees (${mode})"
  echo ""
  echo "- Threshold: ${STALE_DAYS} days"
  echo "- Repo folder: ${REPO_NAME}"
  echo ""

  local seen=0
  local pruned=0
  local candidates=()

  while IFS= read -r repo; do
    [[ -n "${repo}" ]] || continue
    local wt
    wt="$(dirname "${repo}")"
    local age
    age="$(days_old "${wt}")"
    local dirty
    dirty="$(git -C "${repo}" status --porcelain 2>/dev/null || true)"
    if [[ -n "${dirty}" ]]; then
      continue
    fi
    if (( age < STALE_DAYS )); then
      continue
    fi

    local size
    size="$(du -sh "${wt}" 2>/dev/null | awk '{print $1}')"
    candidates+=("${wt}|${age}|${size}")
    seen=$(( seen + 1 ))
    echo "- $(basename "${wt}") | age=${age}d | size=${size} | ${wt}"
  done < <(worktree_repo_paths)

  echo ""
  if [[ "${mode}" == "prune" ]]; then
    if (( seen == 0 )); then
      echo "Pruned stale worktrees: 0"
      return
    fi

    if [[ "${ALLOW_RISKY_PRUNE}" == false ]]; then
      local script_dir hunter_script rc report_path
      script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
      hunter_script="${script_dir}/codex_cherry_pick_hunter.sh"
      if [[ ! -x "${hunter_script}" ]]; then
        echo "Safety gate blocked prune: cherry-pick hunter missing/executable: ${hunter_script}" >&2
        echo "Run: chmod +x ${hunter_script}" >&2
        exit 3
      fi

      set +e
      "${hunter_script}" --worktree-root "${WORKTREE_ROOT}" --repo-name "${REPO_NAME}" --base-ref "${BASE_REF}" --risk-check
      rc=$?
      set -e
      if [[ "${rc}" -eq 3 ]]; then
        report_path="$("${hunter_script}" --worktree-root "${WORKTREE_ROOT}" --repo-name "${REPO_NAME}" --base-ref "${BASE_REF}" --save)"
        echo "Safety gate blocked prune: potential cherry-pick risk detected." >&2
        echo "Review report: ${report_path}" >&2
        echo "If intentional, re-run with --allow-risky-prune" >&2
        exit 3
      elif [[ "${rc}" -ne 0 ]]; then
        echo "Safety gate failed to run cherry-pick hunter (exit ${rc}). Aborting prune." >&2
        exit "${rc}"
      fi
    fi

    local item wt age size
    for item in "${candidates[@]}"; do
      wt="${item%%|*}"
      age="${item#*|}"
      age="${age%%|*}"
      size="${item##*|}"
      rm -rf "${wt}"
      pruned=$(( pruned + 1 ))
      echo "Pruned: $(basename "${wt}") | age=${age}d | size=${size}"
    done
    echo "Pruned stale worktrees: ${pruned}"
  else
    echo "Stale clean worktrees found: ${seen}"
  fi
}

list_or_prune_old_sessions() {
  local mode="$1" # list|prune
  echo "# Codex Old Sessions (${mode})"
  echo ""
  echo "- Threshold: ${SESSION_DAYS} days"
  echo ""

  local roots=("${CODEX_ROOT}/sessions" "${CODEX_ROOT}/archived_sessions")
  local seen=0
  local touched=0
  local total_kb=0

  local root file age kb
  for root in "${roots[@]}"; do
    [[ -d "${root}" ]] || continue
    while IFS= read -r file; do
      [[ -n "${file}" ]] || continue
      age="$(days_old "${file}")"
      if (( age < SESSION_DAYS )); then
        continue
      fi
      kb="$(du -sk "${file}" 2>/dev/null | awk '{print $1}')"
      kb="${kb:-0}"
      total_kb=$(( total_kb + kb ))
      seen=$(( seen + 1 ))
      echo "- age=${age}d | $(human_size "${kb}") | ${file}"
      if [[ "${mode}" == "prune" ]]; then
        rm -f "${file}"
        touched=$(( touched + 1 ))
      fi
    done < <(find "${root}" -type f -name "*.jsonl" 2>/dev/null | sort)
  done

  echo ""
  if [[ "${mode}" == "prune" ]]; then
    echo "Pruned files: ${touched}"
    echo "Freed: $(human_size "${total_kb}")"
  else
    echo "Files older than threshold: ${seen}"
    echo "Potential reclaim: $(human_size "${total_kb}")"
  fi
}

if [[ "${DO_AUDIT}" == true ]]; then
  audit
fi

if [[ "${DO_CACHE_CLEAN}" == true ]]; then
  clean_caches
fi

if [[ "${DO_LIST_STALE}" == true ]]; then
  list_or_prune_stale "list"
fi

if [[ "${DO_PRUNE_STALE}" == true ]]; then
  list_or_prune_stale "prune"
fi

if [[ "${DO_LIST_OLD_SESSIONS}" == true ]]; then
  list_or_prune_old_sessions "list"
fi

if [[ "${DO_PRUNE_OLD_SESSIONS}" == true ]]; then
  list_or_prune_old_sessions "prune"
fi
