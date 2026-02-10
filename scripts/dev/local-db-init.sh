#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
DB_USER="${DB_USER:-scheduler}"
DB_PASSWORD="${DB_PASSWORD:-scheduler}"
DB_NAME="${DB_NAME:-residency_scheduler}"

# shellcheck source=../_native-lib.sh
source "$ROOT_DIR/scripts/_native-lib.sh"

log() {
  printf "[local-db-init] %s\n" "$*"
}

validate_identifier() {
  local value="$1"
  local label="$2"
  if [[ ! "$value" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    log "Invalid ${label}: '${value}'. Use [A-Za-z_][A-Za-z0-9_]*"
    exit 1
  fi
}

validate_password() {
  local value="$1"
  if [ -z "$value" ]; then
    log "DB_PASSWORD must be non-empty."
    exit 1
  fi
  if [[ "$value" == *$'\n'* || "$value" == *$'\r'* ]]; then
    log "DB_PASSWORD cannot contain newline characters."
    exit 1
  fi
}

validate_identifier "$DB_USER" "DB_USER"
validate_identifier "$DB_NAME" "DB_NAME"
validate_password "$DB_PASSWORD"

ensure_local_services() {
  if ! command -v brew >/dev/null 2>&1; then
    log "Homebrew is required to manage local PostgreSQL/Redis services."
    exit 1
  fi

  local pg_formula
  pg_formula="$(detect_brew_postgres_service || true)"
  if [ -z "$pg_formula" ]; then
    pg_formula="postgresql@17"
  fi

  if ! pg_isready -q -h localhost -p 5432 2>/dev/null; then
    log "Starting PostgreSQL service (${pg_formula})"
    brew services start "$pg_formula" >/dev/null
    sleep 2
  fi

  if ! redis-cli ping 2>/dev/null | grep -q PONG; then
    log "Starting Redis service"
    brew services start redis >/dev/null
    sleep 1
  fi

  if ! pg_isready -q -h localhost -p 5432 2>/dev/null; then
    log "PostgreSQL is not reachable on localhost:5432 after startup."
    exit 1
  fi

  if ! redis-cli ping 2>/dev/null | grep -q PONG; then
    log "Redis is not reachable on localhost:6379 after startup."
    exit 1
  fi
}

ensure_local_services

find_psql() {
  if command -v psql >/dev/null 2>&1; then
    command -v psql
    return 0
  fi

  if command -v brew >/dev/null 2>&1; then
    local candidate
    candidate="$(brew --prefix)/opt/libpq/bin/psql"
    if [ -x "$candidate" ]; then
      printf "%s\n" "$candidate"
      return 0
    fi

    local version
    for version in 18 17 16 15; do
      candidate="$(brew --prefix)/opt/postgresql@${version}/bin/psql"
      if [ -x "$candidate" ]; then
        printf "%s\n" "$candidate"
        return 0
      fi
    done
  fi

  return 1
}

PSQL_BIN="$(find_psql || true)"
if [ -z "$PSQL_BIN" ]; then
  log "psql not found. Install postgresql@17 (or @18) and libpq with Homebrew."
  exit 1
fi

log "Using psql binary: $PSQL_BIN"

"$PSQL_BIN" \
  -h localhost \
  -d postgres \
  -v ON_ERROR_STOP=1 \
  -v db_user="$DB_USER" \
  -v db_password="$DB_PASSWORD" \
  -v db_name="$DB_NAME" \
  <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'db_user', :'db_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'db_user')\gexec

SELECT format('ALTER ROLE %I WITH LOGIN PASSWORD %L', :'db_user', :'db_password')
WHERE EXISTS (SELECT FROM pg_roles WHERE rolname = :'db_user')\gexec

SELECT format('CREATE DATABASE %I OWNER %I', :'db_name', :'db_user')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'db_name')\gexec

SELECT format('GRANT ALL PRIVILEGES ON DATABASE %I TO %I', :'db_name', :'db_user')\gexec
SQL

"$PSQL_BIN" -h localhost -d "${DB_NAME}" -v ON_ERROR_STOP=1 <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;
SQL

log "Database role, database, and pgvector extension ensured"

# Ensure Alembic sees the same database credentials we just provisioned.
export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"
export DEBUG="${DEBUG:-true}"

if [ -x "$BACKEND_DIR/.venv/bin/alembic" ]; then
  log "Running Alembic migrations using backend/.venv"
  (
    cd "$BACKEND_DIR"
    .venv/bin/alembic upgrade head
  )
elif command -v uv >/dev/null 2>&1; then
  log "Running Alembic migrations using uv"
  (
    cd "$BACKEND_DIR"
    uv run --python 3.11 --with-requirements requirements.txt alembic upgrade head
  )
else
  log "Running Alembic migrations using system alembic"
  (
    cd "$BACKEND_DIR"
    alembic upgrade head
  )
fi

log "Local database initialization complete"
