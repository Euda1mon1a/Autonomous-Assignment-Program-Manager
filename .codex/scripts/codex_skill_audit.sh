#!/usr/bin/env bash
# Audit local skill definitions for Codex/Claude operator hygiene.
#
# Checks:
# - skill counts by root
# - duplicate skill names across roots
# - missing `name:` frontmatter in SKILL.md
#
# Usage:
#   .codex/scripts/codex_skill_audit.sh
#   .codex/scripts/codex_skill_audit.sh --save

set -euo pipefail

SAVE=false
OUTPUT=""

usage() {
  cat <<'EOF'
Usage:
  .codex/scripts/codex_skill_audit.sh [--save] [--output PATH]

Options:
  --save          Save markdown report to docs/reports/automation/
  --output PATH   Explicit output file path
  -h, --help      Show help
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

tmp_file="$(mktemp)"
trap 'rm -f "${tmp_file}"' EXIT

extract_name() {
  local file="$1"
  awk '
    BEGIN { in_frontmatter=0; seen_start=0; name="" }
    /^---[[:space:]]*$/ {
      if (seen_start == 0) { in_frontmatter=1; seen_start=1; next }
      if (in_frontmatter == 1) { in_frontmatter=0; next }
    }
    in_frontmatter == 1 && $1 == "name:" {
      sub(/^name:[[:space:]]*/, "", $0)
      name=$0
      gsub(/^"|"$/, "", name)
      print name
      exit
    }
  ' "${file}"
}

scan_root() {
  local root="$1"
  local label="$2"
  [[ -d "${root}" ]] || return 0
  while IFS= read -r skill_file; do
    local dir slug name has_name
    dir="$(dirname "${skill_file}")"
    slug="$(basename "${dir}")"
    name="$(extract_name "${skill_file}" || true)"
    if [[ -z "${name}" ]]; then
      name="${slug}"
      has_name=0
    else
      has_name=1
    fi
    printf '%s|%s|%s|%s|%s\n' "${name}" "${slug}" "${skill_file}" "${label}" "${has_name}" >>"${tmp_file}"
  done < <(find "${root}" -type f -name "SKILL.md" | sort)
}

scan_root "${REPO_ROOT}/.codex/skills" "codex"
scan_root "${REPO_ROOT}/.claude/skills" "claude"
scan_root "${HOME}/.claude/skills" "home-claude"

total_count="$(wc -l < "${tmp_file}" | tr -d ' ')"
codex_count="$(awk -F'|' '$4=="codex"{c++} END {print c+0}' "${tmp_file}")"
claude_count="$(awk -F'|' '$4=="claude"{c++} END {print c+0}' "${tmp_file}")"
home_claude_count="$(awk -F'|' '$4=="home-claude"{c++} END {print c+0}' "${tmp_file}")"
missing_name_count="$(awk -F'|' '$5=="0"{c++} END {print c+0}' "${tmp_file}")"

report=""
report+="# Codex Skill Audit"$'\n'
report+=$'\n'
report+="- Timestamp: \`$(date '+%Y-%m-%d %H:%M:%S %Z')\`"$'\n'
report+="- Repo: \`${REPO_ROOT}\`"$'\n'
report+=$'\n'
report+="## Counts"$'\n'
report+=$'\n'
report+="- Total SKILL.md files found: \`${total_count}\`"$'\n'
report+="- .codex/skills: \`${codex_count}\`"$'\n'
report+="- .claude/skills: \`${claude_count}\`"$'\n'
report+="- ~/.claude/skills: \`${home_claude_count}\`"$'\n'
report+="- Missing explicit frontmatter \`name:\` (fallback to folder name): \`${missing_name_count}\`"$'\n'
report+=$'\n'
report+="## Duplicate Skill Names"$'\n'
report+=$'\n'

duplicate_names="$(cut -d'|' -f1 "${tmp_file}" | sort | uniq -d)"
if [[ -z "${duplicate_names}" ]]; then
  report+="- None"$'\n'
else
  while IFS= read -r name; do
    [[ -n "${name}" ]] || continue
    report+="- \`${name}\`"$'\n'
    while IFS= read -r row; do
      [[ -n "${row}" ]] || continue
      label="$(printf '%s\n' "${row}" | cut -d'|' -f4)"
      path="$(printf '%s\n' "${row}" | cut -d'|' -f3)"
      report+="  - [${label}] ${path}"$'\n'
    done < <(awk -F'|' -v n="${name}" '$1==n{print $0}' "${tmp_file}")
  done <<< "${duplicate_names}"
fi

report+=$'\n'
report+="## Quick Actions"$'\n'
report+=$'\n'
report+="- Run \`.codex/scripts/codex_cherry_pick_hunter.sh --save\` before any worktree prune"$'\n'
report+="- Keep high-signal skills in one canonical location to reduce routing ambiguity"$'\n'
report+="- Add/normalize frontmatter \`name:\` where missing for reliable discovery"$'\n'

if [[ "${SAVE}" == true || -n "${OUTPUT}" ]]; then
  out="${OUTPUT}"
  if [[ -z "${out}" ]]; then
    out="docs/reports/automation/codex_skill_audit_$(date '+%Y%m%d-%H%M').md"
  fi
  mkdir -p "$(dirname "${out}")"
  printf '%s\n' "${report}" > "${out}"
  echo "${out}"
else
  printf '%s\n' "${report}"
fi
