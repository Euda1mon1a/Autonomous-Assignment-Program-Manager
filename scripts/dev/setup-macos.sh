#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

SKIP_INSTALL=false
for arg in "$@"; do
  case "$arg" in
    --skip-install)
      SKIP_INSTALL=true
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: scripts/dev/setup-macos.sh [--skip-install]"
      exit 1
      ;;
  esac
done

log() {
  printf "[setup-macos] %s\n" "$*"
}

copy_if_missing() {
  local src="$1"
  local dest="$2"

  if [ ! -f "$src" ]; then
    log "Template missing: $src"
    return 1
  fi

  if [ -f "$dest" ]; then
    log "Keeping existing file: $dest"
  else
    cp "$src" "$dest"
    log "Created $dest from $src"
  fi
}

missing_commands=()
missing_brew_packages=()

if [ "$(uname -s)" != "Darwin" ]; then
  log "This setup script is for macOS only."
  exit 1
fi

if [ "$(uname -m)" != "arm64" ]; then
  log "Apple Silicon required (arm64). Current architecture: $(uname -m)"
  exit 1
fi

log "Verified macOS arm64 runtime"

if ! xcode-select -p >/dev/null 2>&1; then
  missing_commands+=("xcode-select --install")
fi

if ! command -v brew >/dev/null 2>&1; then
  missing_commands+=('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
else
  BREW_PACKAGES=(
    python@3.11
    node@20
    postgresql@15
    redis
    pgvector
    libpq
    pkg-config
    cmake
    openblas
    rust
    jq
  )

  for pkg in "${BREW_PACKAGES[@]}"; do
    if ! brew list --versions "$pkg" >/dev/null 2>&1; then
      missing_brew_packages+=("$pkg")
    fi
  done
fi

if ! command -v npm >/dev/null 2>&1; then
  missing_commands+=("brew install node@20")
fi

if ! command -v uv >/dev/null 2>&1; then
  log "uv not found; setup will use venv+pip fallback."
fi

if [ "${#missing_commands[@]}" -gt 0 ] || [ "${#missing_brew_packages[@]}" -gt 0 ]; then
  log "Missing prerequisites detected. Install these and re-run setup:"

  for cmd in "${missing_commands[@]}"; do
    printf "  %s\n" "$cmd"
  done

  if [ "${#missing_brew_packages[@]}" -gt 0 ]; then
    printf "  brew install"
    for pkg in "${missing_brew_packages[@]}"; do
      printf " %s" "$pkg"
    done
    printf "\n"
  fi

  exit 1
fi

log "All required tools are present"

copy_if_missing "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
copy_if_missing "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
copy_if_missing "$ROOT_DIR/frontend/.env.example" "$ROOT_DIR/frontend/.env.local"
copy_if_missing "$ROOT_DIR/mcp-server/.env.example" "$ROOT_DIR/mcp-server/.env"

"$ROOT_DIR/scripts/dev/local-services-start.sh"

if [ "$SKIP_INSTALL" = false ]; then
  log "Installing backend dependencies"
  if command -v uv >/dev/null 2>&1; then
    uv venv "$ROOT_DIR/backend/.venv" --python 3.11
    uv pip install --python "$ROOT_DIR/backend/.venv/bin/python" -r "$ROOT_DIR/backend/requirements.txt"
  else
    python3.11 -m venv "$ROOT_DIR/backend/.venv"
    "$ROOT_DIR/backend/.venv/bin/pip" install --upgrade pip
    "$ROOT_DIR/backend/.venv/bin/pip" install -r "$ROOT_DIR/backend/requirements.txt"
  fi

  log "Installing frontend dependencies"
  (
    cd "$ROOT_DIR/frontend"
    npm install
  )

  log "Installing MCP server dependencies"
  if command -v uv >/dev/null 2>&1; then
    uv venv "$ROOT_DIR/mcp-server/.venv" --python 3.10
    uv pip install --python "$ROOT_DIR/mcp-server/.venv/bin/python" -e "$ROOT_DIR/mcp-server"
  else
    python3 -m venv "$ROOT_DIR/mcp-server/.venv"
    "$ROOT_DIR/mcp-server/.venv/bin/pip" install --upgrade pip
    "$ROOT_DIR/mcp-server/.venv/bin/pip" install -e "$ROOT_DIR/mcp-server"
  fi
fi

"$ROOT_DIR/scripts/dev/local-db-init.sh"

cat <<'NEXT'

Setup complete.

Next commands:
  make local-start
  make local-status
  make health

Optional quality gates:
  make lint
  make type-check
  make test
NEXT
