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
# "The Great Modron March enforces order across the multiverse.
#  This script enforces order across your type definitions."
#
# Purpose: Ensures frontend TypeScript types match backend Pydantic schemas
# Trigger: Pre-commit when API-related files are modified
#
# How it works:
# 1. Detects if any "wiring" files were modified
# 2. Regenerates TypeScript types from OpenAPI spec
# 3. Compares against committed types
# 4. Blocks commit if drift detected
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

# Check if any staged files match wiring patterns
check_wiring_files_changed() {
    local changed_files
    changed_files=$(git diff --cached --name-only 2>/dev/null || git diff --name-only HEAD~1 2>/dev/null || echo "")

    if [ -z "$changed_files" ]; then
        return 1  # No files changed
    fi

    for pattern in "${WIRING_PATTERNS[@]}"; do
        if echo "$changed_files" | grep -q "$pattern"; then
            return 0  # Wiring file changed
        fi
    done

    return 1  # No wiring files changed
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

# Check if backend is running (needed to fetch OpenAPI spec)
check_backend_available() {
    local api_url="${API_URL:-http://localhost:8000}"
    if curl -s --max-time 2 "${api_url}/openapi.json" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Generate fresh types from OpenAPI spec
generate_types_from_openapi() {
    local api_url="${API_URL:-http://localhost:8000}"
    local output_file="$PROJECT_ROOT/frontend/src/types/api-generated-check.ts"

    log_info "Fetching OpenAPI spec from $api_url..."

    # Generate types using openapi-typescript
    cd "$PROJECT_ROOT/frontend"
    npx openapi-typescript "${api_url}/openapi.json" -o "$output_file" 2>/dev/null

    echo "$output_file"
}

# Compare generated types against existing
compare_types() {
    local generated="$1"
    local existing="$PROJECT_ROOT/frontend/src/types/api-generated.ts"

    if [ ! -f "$existing" ]; then
        log_warn "No existing api-generated.ts found - skipping comparison"
        return 0
    fi

    # Compare (ignoring comments and empty lines, but preserving structure)
    # Do NOT sort - structural changes (property moves) must be detected
    local diff_output
    diff_output=$(diff -u \
        <(grep -v "^//" "$existing" | grep -v "^\s*$") \
        <(grep -v "^//" "$generated" | grep -v "^\s*$") \
        2>/dev/null || true)

    if [ -n "$diff_output" ]; then
        return 1  # Types differ
    fi

    return 0  # Types match
}

# Validate specific type mappings
validate_critical_types() {
    log_info "Validating critical type mappings..."

    local errors=0

    # Check FairnessAuditResponse (lives in useFairness.ts with related types)
    if ! validate_type_exists "FairnessAuditResponse" "frontend/src/hooks/useFairness.ts"; then
        log_error "FairnessAuditResponse not found in useFairness.ts"
        ((errors++))
    fi

    # Check OverallStatus
    if ! validate_type_exists "OverallStatus" "frontend/src/types/resilience.ts"; then
        log_error "OverallStatus not found in resilience.ts"
        ((errors++))
    fi

    # Check DefenseLevel
    if ! validate_type_exists "DefenseLevel" "frontend/src/types/resilience.ts"; then
        log_error "DefenseLevel not found in resilience.ts"
        ((errors++))
    fi

    return $errors
}

validate_type_exists() {
    local type_name="$1"
    local file_path="$PROJECT_ROOT/$2"

    if [ ! -f "$file_path" ]; then
        return 1
    fi

    if grep -q "export.*$type_name" "$file_path" 2>/dev/null; then
        return 0
    fi

    return 1
}

# Check for snake_case in TypeScript interfaces (should be camelCase)
check_naming_convention() {
    log_info "Checking naming conventions..."

    local errors=0
    local ts_files
    ts_files=$(find "$PROJECT_ROOT/frontend/src/types" -name "*.ts" ! -name "api-generated*" 2>/dev/null || echo "")

    for file in $ts_files; do
        # Look for snake_case in interface properties (but not in string literals)
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

# Main validation
run_validation() {
    local errors=0

    # 1. Check naming conventions (always)
    if ! check_naming_convention; then
        ((errors++))
    fi

    # 2. Validate critical types exist
    if ! validate_critical_types; then
        ((errors++))
    fi

    # 3. If backend available, do full OpenAPI comparison
    if check_backend_available; then
        log_info "Backend available - performing full type comparison..."

        local generated_file
        generated_file=$(generate_types_from_openapi)

        if ! compare_types "$generated_file"; then
            log_error "Generated types differ from committed types!"
            log_error "Run 'npm run generate-types' and commit the changes."
            ((errors++))
        else
            log_success "Generated types match committed types"
        fi

        # Cleanup
        rm -f "$generated_file" 2>/dev/null || true
    else
        log_warn "Backend not available - skipping OpenAPI comparison"
        log_warn "To enable full validation, start the backend: docker-compose up -d"
    fi

    return $errors
}

# =============================================================================
# Main
# =============================================================================

main() {
    log_info "Modron March - Frontend-Backend Type Integrity Check"
    echo ""

    # Check if wiring files changed
    if ! check_wiring_files_changed; then
        log_success "No wiring files changed - skipping validation"
        exit 0
    fi

    log_info "Wiring files modified:"
    list_changed_wiring_files
    echo ""

    # Run validation
    if run_validation; then
        log_success "Type contracts validated - Mechanus approves!"
        exit 0
    else
        log_error "Type contract violation detected - Modrons disapprove!"
        echo ""
        log_error "To fix:"
        log_error "  1. Ensure frontend types match backend schemas"
        log_error "  2. Run: cd frontend && npm run generate-types"
        log_error "  3. Check for snake_case in TypeScript interfaces (should be camelCase)"
        log_error "  4. See CLAUDE.md 'API Type Naming Convention' section"
        echo ""
        exit 1
    fi
}

# Run if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
