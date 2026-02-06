#!/usr/bin/env bash
# Print Codex App automation schedule from ~/.codex/automations in a readable table.

set -euo pipefail

ROOT="${HOME}/.codex/automations"

if [[ ! -d "${ROOT}" ]]; then
  echo "Codex automations directory not found: ${ROOT}" >&2
  exit 1
fi

printf "%-28s %-10s %-8s %s\n" "ID" "TIME" "STATUS" "RRULE"
printf "%-28s %-10s %-8s %s\n" "----------------------------" "----------" "--------" "-----"

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
  printf "%-28s %-10s %-8s %s\n" "${id}" "${time}" "${status}" "${rrule}"
done | sort
