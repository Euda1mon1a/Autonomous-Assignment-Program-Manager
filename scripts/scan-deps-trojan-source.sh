#!/usr/bin/env bash
# Supply Chain Defense — Dependency Trojan Source Scanner
#
# Scans installed npm and Python dependencies for invisible Unicode characters
# that could indicate a trojan source attack in downloaded packages.
#
# This catches the *secondary* GlassWorm vector: after compromising a developer's
# machine via VS Code extensions, the malware pushes poisoned code to npm/PyPI
# packages using stolen credentials.
#
# Usage: ./scripts/scan-deps-trojan-source.sh [--npm-only | --python-only]
#
# Note: This is an on-demand scan, not a pre-commit hook. node_modules and
# site-packages are large — expect 15-60s depending on dependency count.

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Same bidi pattern as anti-trojan-source.sh (no variation selectors)
PATTERN=$'[\xe2\x80\xab\xe2\x80\xac\xe2\x80\xad\xe2\x80\xae\xe2\x80\xaa\xe2\x81\xa6\xe2\x81\xa7\xe2\x81\xa8\xe2\x81\xa9\xe2\x80\x8f\xd8\x9c\xe2\x80\x8b\xe2\x80\x8c\xe2\x80\x8d\xef\xbb\xbf]'

SCAN_NPM=true
SCAN_PYTHON=true
FOUND=0
TOTAL_FILES=0

# Parse args
case "${1:-}" in
    --npm-only)   SCAN_PYTHON=false ;;
    --python-only) SCAN_NPM=false ;;
esac

echo "=== Dependency Trojan Source Scanner ==="
echo ""

# Known false positive paths (Unicode test data, locale files, etc.)
# These contain legitimate Unicode for testing/i18n purposes
EXCLUDE_PATTERNS=(
    "*/test*/*"
    "*/tests/*"
    "*/__tests__/*"
    "*/locale/*"
    "*/locales/*"
    "*/i18n/*"
    "*/unicode/*"
    "*/icu-data/*"
    "*/cldr/*"
    "*/.yarn/*"
    "*/CHANGELOG*"
    "*/changelog*"
    "*/CHANGES*"
    "*/History*"
)

build_find_excludes() {
    local excludes=""
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        excludes="$excludes -not -path '$pattern'"
    done
    echo "$excludes"
}

scan_npm() {
    local node_modules="$REPO_ROOT/frontend/node_modules"

    if [ ! -d "$node_modules" ]; then
        echo -e "${YELLOW}SKIP${NC} npm: frontend/node_modules not found (run npm install first)"
        return
    fi

    local pkg_count
    pkg_count=$(find "$node_modules" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${CYAN}Scanning npm packages${NC} ($pkg_count packages in frontend/node_modules)..."

    local npm_found=0
    local npm_files=0

    while IFS= read -r -d '' file; do
        npm_files=$((npm_files + 1))
        local match
        match=$(grep -Pn "$PATTERN" "$file" 2>/dev/null || true)
        if [ -n "$match" ]; then
            # Extract package name from path
            local rel_path="${file#$node_modules/}"
            local pkg_name="${rel_path%%/*}"
            echo -e "  ${RED}ALERT${NC} $pkg_name"
            echo "    File: $rel_path"
            echo "    Match: $(echo "$match" | head -1)"
            npm_found=$((npm_found + 1))
        fi
    done < <(find "$node_modules" -type f \( -name '*.js' -o -name '*.mjs' -o -name '*.cjs' \) \
        -not -path '*/test*/*' \
        -not -path '*/__tests__/*' \
        -not -path '*/locale/*' \
        -not -path '*/locales/*' \
        -not -path '*/i18n/*' \
        -not -path '*/unicode/*' \
        -print0 2>/dev/null)

    TOTAL_FILES=$((TOTAL_FILES + npm_files))
    FOUND=$((FOUND + npm_found))
    echo "  Files scanned: $npm_files | Findings: $npm_found"
    echo ""
}

scan_python() {
    # Find the active Python venv's site-packages
    local site_packages=""

    if [ -n "${VIRTUAL_ENV:-}" ]; then
        site_packages=$(python -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || true)
    else
        # Try pyenv
        site_packages=$(python -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || true)
    fi

    if [ -z "$site_packages" ] || [ ! -d "$site_packages" ]; then
        echo -e "${YELLOW}SKIP${NC} Python: site-packages not found (activate your venv first)"
        return
    fi

    local pkg_count
    pkg_count=$(find "$site_packages" -maxdepth 1 -mindepth 1 -type d -name '*.dist-info' 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${CYAN}Scanning Python packages${NC} ($pkg_count packages in $site_packages)..."

    local py_found=0
    local py_files=0

    while IFS= read -r -d '' file; do
        py_files=$((py_files + 1))
        local match
        match=$(grep -Pn "$PATTERN" "$file" 2>/dev/null || true)
        if [ -n "$match" ]; then
            local rel_path="${file#$site_packages/}"
            local pkg_name="${rel_path%%/*}"
            echo -e "  ${RED}ALERT${NC} $pkg_name"
            echo "    File: $rel_path"
            echo "    Match: $(echo "$match" | head -1)"
            py_found=$((py_found + 1))
        fi
    done < <(find "$site_packages" -type f -name '*.py' \
        -not -path '*/test*/*' \
        -not -path '*/__tests__/*' \
        -not -path '*/locale/*' \
        -not -path '*/locales/*' \
        -not -path '*/i18n/*' \
        -not -path '*/unicode/*' \
        -print0 2>/dev/null)

    TOTAL_FILES=$((TOTAL_FILES + py_files))
    FOUND=$((FOUND + py_found))
    echo "  Files scanned: $py_files | Findings: $py_found"
    echo ""
}

# Run scans
if $SCAN_NPM; then scan_npm; fi
if $SCAN_PYTHON; then scan_python; fi

echo "---"
echo "Total files scanned: $TOTAL_FILES"

if [ "$FOUND" -gt 0 ]; then
    echo ""
    echo -e "${RED}FOUND $FOUND file(s) with invisible Unicode in dependencies.${NC}"
    echo ""
    echo "Recommended actions:"
    echo "  1. Identify the package and check its npm/PyPI page for known compromises"
    echo "  2. Check if the package has provenance attestations: npm audit signatures"
    echo "  3. Pin the last-known-good version in package.json / requirements.txt"
    echo "  4. Report to the package maintainer and npm/PyPI security team"
    exit 1
else
    echo -e "${GREEN}No invisible Unicode found in dependencies.${NC}"
    exit 0
fi
