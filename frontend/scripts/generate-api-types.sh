#!/bin/bash
# ============================================================
# Script: generate-api-types.sh
# Purpose: Generate TypeScript types from FastAPI OpenAPI spec
#
# PARADIGM: Generated types ARE the source of truth.
# Manual types in api.ts are DEPRECATED - use api-generated.ts.
#
# Usage:
#   ./scripts/generate-api-types.sh           # Generate types
#   ./scripts/generate-api-types.sh --check   # Check for drift only
#
# Requirements:
#   - Backend running at localhost:8000 (or BACKEND_URL env var)
#   - openapi-typescript installed (npm install -D openapi-typescript)
#
# Output:
#   frontend/src/types/api-generated.ts
#   - Schema properties: camelCase (matches axios response transformation)
#   - Query/path params: snake_case (matches URL requirements)
#
# History:
#   - 2026-01-17: Initial version (snake_case output)
#   - 2026-01-20: Added camelCase post-processing
#   - 2026-01-20: Fixed to only convert schemas, not query/path params
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

echo -e "${CYAN}OpenAPI Type Generator (Smart camelCase)${NC}"
echo "==========================================="

# Check if backend is running
echo -n "Checking backend at $BACKEND_URL... "
if ! curl -s "$BACKEND_URL/health" >/dev/null 2>&1; then
    echo -e "${RED}FAILED${NC}"
    echo ""
    echo "Backend not running. Start it with:"
    echo "  docker-compose up -d backend"
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

# Generate types (snake_case initially)
echo -n "Generating TypeScript types... "
npx openapi-typescript "$OPENAPI_URL" -o "$TEMP_FILE.snake" 2>/dev/null

if [ ! -f "$TEMP_FILE.snake" ]; then
    echo -e "${RED}FAILED${NC}"
    echo "openapi-typescript failed to generate types"
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Smart camelCase conversion - ONLY for schema properties
echo -n "Converting schema properties to camelCase... "

node -e "
const fs = require('fs');
const content = fs.readFileSync('$TEMP_FILE.snake', 'utf8');

// Split the file into sections
// We need to find the 'schemas:' section inside 'components' interface
// and ONLY convert snake_case to camelCase there

let result = '';
let inSchemas = false;
let braceDepth = 0;
let schemasStartDepth = 0;

const lines = content.split('\n');

for (let i = 0; i < lines.length; i++) {
  let line = lines[i];

  // Track when we enter 'schemas:' section
  // Look for '    schemas: {' pattern (4 spaces = inside components interface)
  if (/^\s{4}schemas:\s*\{/.test(line)) {
    inSchemas = true;
    schemasStartDepth = (line.match(/\{/g) || []).length - (line.match(/\}/g) || []).length;
    braceDepth = schemasStartDepth;
  }

  // If we're in schemas section, convert snake_case properties to camelCase
  if (inSchemas) {
    // Convert property definitions: prop_name: or prop_name?: or \"prop_name\":
    line = line.replace(
      /^(\s*)([a-z][a-z0-9]*(?:_[a-z0-9]+)+)(\??:\s)/g,
      (match, indent, prop, suffix) => {
        const camel = prop.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase());
        return indent + camel + suffix;
      }
    );

    // Also convert quoted property names: \"prop_name\":
    line = line.replace(
      /\"([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\"(\??:)/g,
      (match, prop, suffix) => {
        const camel = prop.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase());
        return '\"' + camel + '\"' + suffix;
      }
    );

    // Track brace depth to know when we exit schemas
    braceDepth += (line.match(/\{/g) || []).length;
    braceDepth -= (line.match(/\}/g) || []).length;

    // Exit schemas section when we close all its braces
    if (braceDepth <= 0) {
      inSchemas = false;
    }
  }

  result += line + '\n';
}

// Remove trailing newline duplication
result = result.replace(/\n+$/, '\n');

fs.writeFileSync('$TEMP_FILE', result);

// Count conversions for reporting
const originalSnake = (content.match(/[a-z][a-z0-9]*_[a-z0-9]+/g) || []).length;
const resultSnake = (result.match(/[a-z][a-z0-9]*_[a-z0-9]+/g) || []).length;
const converted = originalSnake - resultSnake;

console.log(converted + ' properties converted');
"

rm "$TEMP_FILE.snake"

if [ ! -f "$TEMP_FILE" ]; then
    echo -e "${RED}FAILED${NC}"
    echo "camelCase conversion failed"
    exit 1
fi

LINES=$(wc -l < "$TEMP_FILE" | tr -d ' ')
echo -e "${GREEN}OK${NC} ($LINES lines)"

# Verify query params stayed snake_case
echo -n "Verifying query params are snake_case... "
QUERY_CAMEL=$(grep -E "query\?:" -A 20 "$TEMP_FILE" | grep -E "^\s+[a-z]+[A-Z]" | head -5 || true)
if [ -n "$QUERY_CAMEL" ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo "Some query params may have been converted:"
    echo "$QUERY_CAMEL"
else
    echo -e "${GREEN}OK${NC}"
fi

# Add header comment
HEADER="/**
 * AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY
 *
 * Generated from: $OPENAPI_URL
 * Generated at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
 * Generator: openapi-typescript + smart camelCase post-processing
 *
 * To regenerate:
 *   cd frontend && npm run generate:types
 *
 * PARADIGM: This file IS the source of truth for API types.
 *
 * Property Naming:
 * - Schema properties (components.schemas.*): camelCase
 *   → Matches axios interceptor output for response bodies
 * - Query parameters: snake_case
 *   → Must match URL format (axios doesn't convert URLs)
 * - Path parameters: snake_case
 *   → Must match URL format
 *
 * DO NOT manually edit this file. To change types:
 * 1. Modify backend Pydantic schemas
 * 2. Run: npm run generate:types
 * 3. Commit both backend and frontend changes together
 *
 * See CLAUDE.md 'OpenAPI Type Contract' section for details.
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
    EXISTING_HASH=$(tail -n +30 "$OUTPUT_FILE" | md5sum | cut -d' ' -f1)
    NEW_HASH=$(tail -n +30 "$TEMP_FILE" | md5sum | cut -d' ' -f1)

    if [ "$EXISTING_HASH" = "$NEW_HASH" ]; then
        echo -e "${GREEN}✓ No drift detected - types are in sync!${NC}"
        rm "$TEMP_FILE"
        exit 0
    else
        echo -e "${RED}✗ SCHEMA DRIFT DETECTED!${NC}"
        echo ""
        echo "Backend schemas have changed but types weren't regenerated."
        echo ""
        echo "To fix:"
        echo "  cd frontend && npm run generate:types"
        echo ""
        echo "Then commit both backend schema changes and regenerated types."
        echo ""
        echo "To see diff:"
        echo "  diff $OUTPUT_FILE $TEMP_FILE | head -100"
        rm "$TEMP_FILE"
        exit 1
    fi
fi

# Normal mode - write output
mv "$TEMP_FILE" "$OUTPUT_FILE"
echo ""
echo -e "${GREEN}✓ Types generated successfully!${NC}"
echo "Output: $OUTPUT_FILE"
echo ""
echo -e "${CYAN}Summary:${NC}"
echo "  - Schema properties: camelCase (for response data)"
echo "  - Query/path params: snake_case (for URLs)"
echo ""
echo -e "${CYAN}REMINDER: Commit this file with your backend schema changes.${NC}"
