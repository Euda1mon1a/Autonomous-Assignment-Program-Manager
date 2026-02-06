#!/usr/bin/env bash
# shellcheck shell=bash
#
# Codex local setup loader:
# - loads repo .env and .env.codex (if present)
# - falls back to macOS Keychain for common API key names when env is missing/placeholder
#
# Usage:
#   source .codex/setup.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

load_env_file() {
  local file="$1"
  [[ -f "${file}" ]] || return 0
  set -a
  # shellcheck disable=SC1090
  source "${file}"
  set +a
}

is_placeholder() {
  local value="${1:-}"
  case "${value}" in
    ""|"<redacted>"|"<REDACTED>"|"<placeholder>"|"<PLACEHOLDER>"|\
    "your-key-here"|"pplx-your-key-here"|"sk-your-key-here"|\
    "REPLACE_ME"|"replace_me"|"changeme"|"CHANGEME"|"***")
      return 0
      ;;
  esac
  return 1
}

keychain_lookup() {
  local service="$1"
  security find-generic-password -s "${service}" -w 2>/dev/null || true
}

get_var_value() {
  local var_name="$1"
  eval "printf '%s' \"\${${var_name}:-}\""
}

load_key_from_keychain() {
  local var_name="$1"
  shift

  local current
  current="$(get_var_value "${var_name}")"
  if [[ -n "${current}" ]] && ! is_placeholder "${current}"; then
    return 0
  fi

  local service value
  for service in "$@"; do
    value="$(keychain_lookup "${service}")"
    if [[ -n "${value}" ]] && ! is_placeholder "${value}"; then
      export "${var_name}=${value}"
      return 0
    fi
  done
  return 1
}

# 1) Load repo-local environment files first.
load_env_file "${REPO_ROOT}/.env"
load_env_file "${REPO_ROOT}/.env.codex"

# 2) Keychain fallback for common key names.
if command -v security >/dev/null 2>&1; then
  load_key_from_keychain OPENAI_API_KEY OPENAI_API_KEY openai-api-key OPENAI openai || true
  load_key_from_keychain ANTHROPIC_API_KEY ANTHROPIC_API_KEY anthropic-api-key ANTHROPIC anthropic || true
  load_key_from_keychain PERPLEXITY_API_KEY PERPLEXITY_API_KEY perplexity-api-key PERPLEXITY perplexity || true
  load_key_from_keychain MCP_API_KEY MCP_API_KEY mcp-api-key mcp_api_key || true
fi

if [[ "${CODEX_SETUP_VERBOSE:-0}" == "1" ]]; then
  for v in OPENAI_API_KEY ANTHROPIC_API_KEY PERPLEXITY_API_KEY MCP_API_KEY; do
    value="$(get_var_value "${v}")"
    if [[ -n "${value}" ]] && ! is_placeholder "${value}"; then
      echo "[codex setup] ${v}=set"
    else
      echo "[codex setup] ${v}=unset"
    fi
  done
fi

export CODEX_SETUP_LOADED=1
