#!/usr/bin/env bash
set -euo pipefail

BLOCK_NUMBER="${BLOCK_NUMBER:-10}"
ACADEMIC_YEAR="${ACADEMIC_YEAR:-2025}"
START_DATE="${START_DATE:-2026-03-12}"
END_DATE="${END_DATE:-2026-04-08}"

DB_CONTAINER="${DB_CONTAINER:-residency-scheduler-db}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-residency-scheduler-backend}"
API_URL="${API_URL:-http://localhost:8000/health}"

info() { echo "==> $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

run_psql() {
  docker exec "$DB_CONTAINER" psql -U scheduler -d residency_scheduler -tA -F',' -c "$1"
}

info "Block 10 preflight starting (block=${BLOCK_NUMBER}, ay=${ACADEMIC_YEAR})"

command -v docker >/dev/null 2>&1 || die "docker is required"
command -v curl >/dev/null 2>&1 || die "curl is required"

info "Checking containers..."
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
  if docker ps --format '{{.Names}}' | grep -q "^scheduler-local-db$"; then
    DB_CONTAINER="scheduler-local-db"
    info "Detected local DB container: ${DB_CONTAINER}"
  else
    die "DB container not running: ${DB_CONTAINER}"
  fi
fi
if ! docker ps --format '{{.Names}}' | grep -q "^${BACKEND_CONTAINER}$"; then
  if docker ps --format '{{.Names}}' | grep -q "^scheduler-local-backend$"; then
    BACKEND_CONTAINER="scheduler-local-backend"
    info "Detected local backend container: ${BACKEND_CONTAINER}"
  else
    die "Backend container not running: ${BACKEND_CONTAINER}"
  fi
fi

info "Checking API health..."
health="$(curl -sf "${API_URL}")" || die "API health check failed: ${API_URL}"
echo "$health" | grep -q '"status":"healthy"' || die "API not healthy: ${health}"
echo "$health" | grep -q '"database":"connected"' || die "DB not connected: ${health}"

info "Checking people roster..."
roster="$(run_psql "SELECT
  SUM(CASE WHEN type='resident' THEN 1 ELSE 0 END) AS residents,
  SUM(CASE WHEN type='faculty' AND (faculty_role != 'adjunct' OR faculty_role IS NULL) THEN 1 ELSE 0 END) AS faculty_non_adjunct,
  SUM(CASE WHEN type='faculty' AND faculty_role = 'adjunct' THEN 1 ELSE 0 END) AS faculty_adjunct
FROM people;")"
IFS=',' read -r residents faculty_non_adjunct faculty_adjunct <<< "$roster"
[[ -n "${residents:-}" ]] || die "Unable to read people counts"
info "Residents=${residents}, Faculty(non-adjunct)=${faculty_non_adjunct}, Adjunct=${faculty_adjunct}"

info "Checking block assignments..."
block_assignments="$(run_psql "SELECT COUNT(*) FROM block_assignments WHERE block_number=${BLOCK_NUMBER} AND academic_year=${ACADEMIC_YEAR};")"
[[ "$block_assignments" -eq "$residents" ]] || die "Block assignments (${block_assignments}) != residents (${residents}) for block ${BLOCK_NUMBER} AY ${ACADEMIC_YEAR}"

info "Checking activities count..."
activity_count="$(run_psql "SELECT COUNT(*) FROM activities;")"
[[ "$activity_count" -ge 83 ]] || die "Activities count too low: ${activity_count} (<83)"

info "Checking required activity codes..."
missing_activities="$(run_psql "WITH required(code) AS (
  VALUES
    ('LEC-PM'), ('LEC'), ('ADV'), ('C'), ('C-I'),
    ('CALL'), ('PCAT'), ('DO'),
    ('FMIT'), ('NF'), ('IM'), ('PedW'), ('aSM'),
    ('W'), ('LV'), ('OFF'), ('HOL')
)
SELECT code FROM required
WHERE NOT EXISTS (
  SELECT 1 FROM activities a
  WHERE a.code = required.code OR a.display_abbreviation = required.code
);")"
if [[ -n "${missing_activities}" ]]; then
  die "Missing activities: ${missing_activities//$'\n'/, }"
fi

info "Checking placeholder rotation templates..."
missing_templates="$(run_psql "WITH required(abbrev) AS (
  VALUES
    ('W-AM'), ('W-PM'), ('LV-AM'), ('LV-PM'),
    ('OFF-AM'), ('OFF-PM'), ('HOL-AM'), ('HOL-PM'),
    ('LEC-PM'), ('LEC'), ('ADV'), ('C')
)
SELECT abbrev FROM required
WHERE NOT EXISTS (
  SELECT 1 FROM rotation_templates rt
  WHERE rt.abbreviation = required.abbrev
);")"
if [[ -n "${missing_templates}" ]]; then
  die "Missing rotation templates: ${missing_templates//$'\n'/, }"
fi

info "Checking weekly_patterns for NULL activity_id..."
null_patterns="$(run_psql "SELECT COUNT(*) FROM weekly_patterns WHERE activity_id IS NULL;")"
[[ "$null_patterns" -eq 0 ]] || die "weekly_patterns has NULL activity_id: ${null_patterns}"

info "Checking date-range coverage sanity..."
range_assignments="$(run_psql "SELECT COUNT(*) FROM half_day_assignments WHERE date >= '${START_DATE}' AND date <= '${END_DATE}';")"
info "Existing half_day_assignments in range: ${range_assignments}"

info "Preflight PASSED"
