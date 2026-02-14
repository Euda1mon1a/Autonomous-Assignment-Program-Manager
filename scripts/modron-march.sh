#!/bin/bash
# =============================================================================
# MODRON MARCH - Frontend-Backend Type Integrity Validator
# =============================================================================
#
# Named after the Modrons of D&D - lawful constructs from Mechanus (the plane
# of absolute order) who enforce cosmic law. Every 289 years they march through
# the planes ensuring order is maintained. Like Modrons, this hook ensures
# frontend-backend type contracts remain in perfect mechanical harmony.
#
# Purpose: Ensures frontend TypeScript types match backend Pydantic schemas
# Trigger: Pre-commit when API-related files are modified
#
# Two validation modes:
#   1. ONLINE (backend running): Regenerate types, compare against committed
#   2. OFFLINE (backend down): Compare committed hash file against actual content
#
# Wiring files (trigger validation when changed):
# - backend/app/schemas/*.py (Pydantic models)
# - backend/app/api/routes/*.py (API endpoints)
# - frontend/src/types/api.ts (manual types)
# - frontend/src/types/resilience.ts (domain types)
# - frontend/src/hooks/use*.ts (API hooks)
# - frontend/src/lib/api.ts (API client)
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

GENERATED_TYPES="$PROJECT_ROOT/frontend/src/types/api-generated.ts"
HASH_FILE="$PROJECT_ROOT/frontend/src/types/.api-generated.hash"

# Wiring file patterns (files that affect API contract)
WIRING_PATTERNS=(
    "backend/app/schemas/"
    "backend/app/api/routes/"
    "frontend/src/types/api"
    "frontend/src/types/resilience"
    "frontend/src/hooks/use"
    "frontend/src/lib/api.ts"
    "frontend/src/lib/hooks.ts"
)

# =============================================================================
# Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[MODRON]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[MODRON]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[MODRON]${NC} $1"
}

log_error() {
    echo -e "${RED}[MODRON]${NC} $1"
}

# Cross-platform md5
content_hash() {
    if command -v md5 >/dev/null 2>&1; then
        md5 -q
    else
        md5sum | cut -d' ' -f1
    fi
}

# Check if any staged files match wiring patterns
check_wiring_files_changed() {
    local changed_files
    changed_files=$(git diff --cached --name-only 2>/dev/null || git diff --name-only HEAD~1 2>/dev/null || echo "")

    if [ -z "$changed_files" ]; then
        return 1
    fi

    for pattern in "${WIRING_PATTERNS[@]}"; do
        if echo "$changed_files" | grep -q "$pattern"; then
            return 0
        fi
    done

    return 1
}

# List which wiring files changed
list_changed_wiring_files() {
    local changed_files
    changed_files=$(git diff --cached --name-only 2>/dev/null || git diff --name-only HEAD~1 2>/dev/null || echo "")

    echo "$changed_files" | while read -r file; do
        for pattern in "${WIRING_PATTERNS[@]}"; do
            if [[ "$file" == *"$pattern"* ]]; then
                echo "  - $file"
                break
            fi
        done
    done
}

# Check if backend is running
check_backend_available() {
    local api_url="${API_URL:-http://localhost:8000}"
    if curl -s --max-time 2 "${api_url}/openapi.json" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# ONLINE: Generate and compare types via frontend generator
run_online_check() {
    local api_url="${API_URL:-http://localhost:8000}"

    log_info "Backend available — running full type regeneration check..."
    (
        cd "$PROJECT_ROOT/frontend"
        BACKEND_URL="$api_url" ./scripts/generate-api-types.sh --check
    )
}

# OFFLINE: Compare committed hash against actual file content
run_offline_check() {
    if [ ! -f "$GENERATED_TYPES" ]; then
        log_error "api-generated.ts not found"
        return 1
    fi

    if [ ! -f "$HASH_FILE" ]; then
        log_warn "No hash file found at $HASH_FILE"
        log_warn "Generate types first: cd frontend && npm run generate:types"
        log_warn "Skipping offline hash check (hash file not yet created)"
        return 0
    fi

    local committed_hash
    committed_hash=$(cat "$HASH_FILE" | tr -d '[:space:]')

    local actual_hash
    actual_hash=$(tail -n +30 "$GENERATED_TYPES" | content_hash | tr -d '[:space:]')

    if [ "$committed_hash" = "$actual_hash" ]; then
        log_success "Offline hash check passed — types match committed hash"
        return 0
    else
        log_error "Hash mismatch! api-generated.ts was modified without regenerating."
        log_error "  Committed hash: $committed_hash"
        log_error "  Actual hash:    $actual_hash"
        log_error ""
        log_error "To fix: cd frontend && npm run generate:types"
        log_error "Then commit both api-generated.ts and .api-generated.hash"
        return 1
    fi
}

# Check for snake_case in TypeScript interfaces (should be camelCase)
check_naming_convention() {
    log_info "Checking naming conventions..."

    local errors=0
    local ts_files
    ts_files=$(find "$PROJECT_ROOT/frontend/src/types" -name "*.ts" ! -name "api-generated*" ! -name ".api-generated*" 2>/dev/null || echo "")

    for file in $ts_files; do
        local snake_case_props
        snake_case_props=$(grep -En "^\s+[a-z]+_[a-z]+[?:]" "$file" 2>/dev/null | grep -v "'" | grep -v '"' || true)

        if [ -n "$snake_case_props" ]; then
            log_error "snake_case properties found in $file:"
            echo "$snake_case_props" | head -5
            ((errors++))
        fi
    done

    return $errors
}

# Validate specific type mappings
validate_critical_types() {
    log_info "Validating critical type mappings..."

    local errors=0

    if ! grep -q "export.*FairnessAuditResponse" "$PROJECT_ROOT/frontend/src/types/resilience.ts" 2>/dev/null; then
        log_error "FairnessAuditResponse not found in resilience.ts"
        ((errors++))
    fi

    if ! grep -q "export.*OverallStatus" "$PROJECT_ROOT/frontend/src/types/resilience.ts" 2>/dev/null; then
        log_error "OverallStatus not found in resilience.ts"
        ((errors++))
    fi

    if ! grep -q "export.*DefenseLevel" "$PROJECT_ROOT/frontend/src/types/resilience.ts" 2>/dev/null; then
        log_error "DefenseLevel not found in resilience.ts"
        ((errors++))
    fi

    return $errors
}

# =============================================================================
# Main
# =============================================================================

main() {
    log_info "Modron March — Frontend-Backend Type Integrity Check"
    echo ""

    # Check if wiring files changed
    if ! check_wiring_files_changed; then
        log_success "No wiring files changed — skipping validation"
        exit 0
    fi

    log_info "Wiring files modified:"
    list_changed_wiring_files
    echo ""

    local errors=0

    # 1. Naming convention check (always, no backend needed)
    if ! check_naming_convention; then
        ((errors++))
    fi

    # 2. Critical types exist (always, no backend needed)
    if ! validate_critical_types; then
        ((errors++))
    fi

    # 3. Type drift check — online or offline
    if check_backend_available; then
        if ! run_online_check; then
            log_error "Run 'cd frontend && npm run generate:types' and commit the changes."
            ((errors++))
        fi
    else
        log_warn "Backend not running — using offline hash check"
        if ! run_offline_check; then
            ((errors++))
        fi
    fi

    # Result
    if [ $errors -gt 0 ]; then
        echo ""
        log_error "Type contract violation detected — Modrons disapprove!"
        echo ""
        log_error "To fix:"
        log_error "  1. Start backend if needed"
        log_error "  2. Run: cd frontend && npm run generate:types"
        log_error "  3. Commit both api-generated.ts and .api-generated.hash"
        log_error "  4. See CLAUDE.md 'OpenAPI Type Contract' section"
        echo ""
        exit 1
    else
        log_success "Type contracts validated — Mechanus approves!"
        exit 0
    fi
}

# Run if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
