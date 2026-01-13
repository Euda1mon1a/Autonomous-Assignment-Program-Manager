#!/bin/bash
# ============================================================
# Script: generate-api-types.sh
# Purpose: Generate TypeScript types from FastAPI OpenAPI spec
#
# Usage:
#   ./scripts/generate-api-types.sh           # Uses running backend
#   ./scripts/generate-api-types.sh --check   # Check for drift only
#
# Requirements:
#   - Backend running at localhost:8000 (or BACKEND_URL env var)
#   - openapi-typescript installed (npm install -D openapi-typescript)
#
# Output:
#   frontend/src/types/api-generated.ts
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
OPENAPI_URL="$BACKEND_URL/openapi.json"
OUTPUT_FILE="src/types/api-generated.ts"
TEMP_FILE="/tmp/api-generated-new.ts"
CHECK_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            CHECK_MODE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}OpenAPI Type Generator${NC}"
echo "======================"

# Check if backend is running
echo -n "Checking backend at $BACKEND_URL... "
if ! curl -s "$BACKEND_URL/health" >/dev/null 2>&1; then
    echo -e "${RED}FAILED${NC}"
    echo ""
    echo "Backend not running. Start it with:"
    echo "  cd backend && uvicorn app.main:app --reload"
    echo ""
    echo "Or set BACKEND_URL environment variable:"
    echo "  BACKEND_URL=http://your-backend:8000 ./scripts/generate-api-types.sh"
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Fetch OpenAPI spec
echo -n "Fetching OpenAPI spec... "
SPEC=$(curl -s "$OPENAPI_URL" 2>/dev/null)
if [ -z "$SPEC" ]; then
    echo -e "${RED}FAILED${NC}"
    echo "Could not fetch $OPENAPI_URL"
    exit 1
fi

# Validate it's JSON
if ! echo "$SPEC" | jq empty 2>/dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo "Invalid JSON from $OPENAPI_URL"
    exit 1
fi

PATHS_COUNT=$(echo "$SPEC" | jq '.paths | length')
SCHEMAS_COUNT=$(echo "$SPEC" | jq '.components.schemas | length')
echo -e "${GREEN}OK${NC} ($PATHS_COUNT paths, $SCHEMAS_COUNT schemas)"

# Generate types
echo -n "Generating TypeScript types... "
npx openapi-typescript "$OPENAPI_URL" -o "$TEMP_FILE" 2>/dev/null

if [ ! -f "$TEMP_FILE" ]; then
    echo -e "${RED}FAILED${NC}"
    echo "openapi-typescript failed to generate types"
    exit 1
fi

LINES=$(wc -l < "$TEMP_FILE" | tr -d ' ')
echo -e "${GREEN}OK${NC} ($LINES lines)"

# Add header comment
HEADER="/**
 * AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY
 *
 * Generated from: $OPENAPI_URL
 * Generated at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
 * Generator: openapi-typescript
 *
 * To regenerate:
 *   npm run generate:types
 *
 * This file contains TypeScript types matching the backend Pydantic schemas.
 * The axios interceptor converts snake_case <-> camelCase automatically,
 * but these types reflect the WIRE format (snake_case).
 *
 * For application code, prefer using the manually-maintained types in:
 *   src/types/admin-scheduling.ts
 *   src/types/schedule.ts
 *   etc.
 *
 * Use these generated types for:
 *   - Validating manual types match backend
 *   - Reference when updating manual types
 *   - Direct API usage where manual types don't exist
 */

"

echo "$HEADER" > "$TEMP_FILE.header"
cat "$TEMP_FILE" >> "$TEMP_FILE.header"
mv "$TEMP_FILE.header" "$TEMP_FILE"

# Check mode - compare only
if [ "$CHECK_MODE" = true ]; then
    echo ""
    echo -e "${CYAN}Running drift check...${NC}"

    if [ ! -f "$OUTPUT_FILE" ]; then
        echo -e "${YELLOW}WARNING: $OUTPUT_FILE does not exist${NC}"
        echo "Run without --check to generate it."
        exit 1
    fi

    # Compare (ignoring timestamp in header)
    EXISTING_HASH=$(tail -n +20 "$OUTPUT_FILE" | md5sum | cut -d' ' -f1)
    NEW_HASH=$(tail -n +20 "$TEMP_FILE" | md5sum | cut -d' ' -f1)

    if [ "$EXISTING_HASH" = "$NEW_HASH" ]; then
        echo -e "${GREEN}No drift detected - types are in sync!${NC}"
        rm "$TEMP_FILE"
        exit 0
    else
        echo -e "${RED}DRIFT DETECTED!${NC}"
        echo ""
        echo "Backend schemas have changed. Regenerate types with:"
        echo "  npm run generate:types"
        echo ""
        echo "Or diff the changes:"
        echo "  diff $OUTPUT_FILE $TEMP_FILE | head -50"
        rm "$TEMP_FILE"
        exit 1
    fi
fi

# Normal mode - write output
mv "$TEMP_FILE" "$OUTPUT_FILE"
echo ""
echo -e "${GREEN}Types generated successfully!${NC}"
echo "Output: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "  1. Review the generated types"
echo "  2. Update manual types in src/types/ if needed"
echo "  3. Commit both files together"
