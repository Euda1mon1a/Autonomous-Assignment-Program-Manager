#!/usr/bin/env bash
# Print Codex App automation schedule from ~/.codex/automations in a readable table.

set -euo pipefail

ROOT="${HOME}/.codex/automations"
WINDOW_START="01:00"
WINDOW_END="02:00"
FAIL_ON_COLLISION=false
MAX_PER_MINUTE=5

usage() {
  cat <<'EOF'
Usage:
  .codex/scripts/codex_app_schedule_status.sh [options]

Options:
  --fail-on-collision    Exit non-zero when active automations exceed max per minute
  --max-per-minute N     Maximum allowed active automations per minute (default: 5)
  -h, --help             Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fail-on-collision)
      FAIL_ON_COLLISION=true
      shift
      ;;
    --max-per-minute)
      MAX_PER_MINUTE="${2:-}"
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

if ! [[ "${MAX_PER_MINUTE}" =~ ^[0-9]+$ ]]; then
  echo "--max-per-minute must be a non-negative integer: ${MAX_PER_MINUTE}" >&2
  exit 2
fi

if [[ ! -d "${ROOT}" ]]; then
  echo "Codex automations directory not found: ${ROOT}" >&2
  exit 1
fi

rows_file="$(mktemp)"
trap 'rm -f "${rows_file}"' EXIT

for f in "${ROOT}"/*/automation.toml; do
  [[ -f "${f}" ]] || continue
  id="$(rg '^id = ' "${f}" | cut -d'"' -f2)"
  status="$(rg '^status = ' "${f}" | cut -d'"' -f2)"
  rrule="$(rg '^rrule = ' "${f}" | cut -d'"' -f2)"
  hour="$(echo "${rrule}" | sed -n 's/.*BYHOUR=\([0-9][0-9]*\).*/\1/p')"
  minute="$(echo "${rrule}" | sed -n 's/.*BYMINUTE=\([0-9][0-9]*\).*/\1/p')"
  if [[ -n "${hour}" && -n "${minute}" ]]; then
    time="$(printf "%02d:%02d" "${hour}" "${minute}")"
  else
    time="(n/a)"
  fi
  printf "%s\t%s\t%s\t%s\n" "${time}" "${id}" "${status}" "${rrule}" >>"${rows_file}"
done

printf "%-28s %-10s %-8s %s\n" "ID" "TIME" "STATUS" "RRULE"
printf "%-28s %-10s %-8s %s\n" "----------------------------" "----------" "--------" "-----"

sort -t $'\t' -k1,1 -k2,2 "${rows_file}" | while IFS=$'\t' read -r time id status rrule; do
  printf "%-28s %-10s %-8s %s\n" "${id}" "${time}" "${status}" "${rrule}"
done

active_total="$(
  awk -F $'\t' '$3 == "ACTIVE" { count += 1 } END { print count + 0 }' "${rows_file}"
)"
active_in_window="$(
  awk -F $'\t' -v start="${WINDOW_START}" -v end="${WINDOW_END}" '
    $3 == "ACTIVE" && $1 ~ /^[0-2][0-9]:[0-5][0-9]$/ && $1 >= start && $1 < end { count += 1 }
    END { print count + 0 }
  ' "${rows_file}"
)"
busiest_count="$(
  awk -F $'\t' '
    $3 == "ACTIVE" && $1 ~ /^[0-2][0-9]:[0-5][0-9]$/ {
      per_minute[$1] += 1
      if (per_minute[$1] > max) {
        max = per_minute[$1]
      }
    }
    END { print max + 0 }
  ' "${rows_file}"
)"
busiest_minute_name="$(
  awk -F $'\t' '
    $3 == "ACTIVE" && $1 ~ /^[0-2][0-9]:[0-5][0-9]$/ {
      per_minute[$1] += 1
      if (per_minute[$1] > max) {
        max = per_minute[$1]
        minute = $1
      }
    }
    END {
      printf "%s", (max > 0 ? minute : "n/a")
    }
  ' "${rows_file}"
)"
collisions="$(
  awk -F $'\t' '
    $3 == "ACTIVE" && $1 ~ /^[0-2][0-9]:[0-5][0-9]$/ { per_minute[$1] += 1 }
    END {
      for (minute in per_minute) {
        if (per_minute[minute] > 1) {
          printf "%s (%d)\n", minute, per_minute[minute]
        }
      }
    }
  ' "${rows_file}" | sort
)"

echo ""
echo "Summary:"
echo "  Active automations: ${active_total}"
echo "  Active in ${WINDOW_START}-${WINDOW_END}: ${active_in_window}"
echo "  Busiest minute: ${busiest_minute_name} (${busiest_count})"
if [[ -n "${collisions}" ]]; then
  echo "  Minute collisions:"
  while IFS= read -r line; do
    echo "    - ${line}"
  done <<<"${collisions}"
else
  echo "  Minute collisions: none"
fi

if [[ "${FAIL_ON_COLLISION}" == true && "${busiest_count}" -gt "${MAX_PER_MINUTE}" ]]; then
  echo ""
  echo "Collision threshold exceeded: busiest minute has ${busiest_count} active automations (max ${MAX_PER_MINUTE})." >&2
  exit 3
fi
