#!/usr/bin/env bash
# GlassWorm Defense — VS Code Extension Scanner
#
# Scans installed VS Code/Cursor/Antigravity extensions for invisible Unicode
# characters used by GlassWorm-style attacks. These attacks embed bidi control
# characters in extension source to make malicious code appear benign.
#
# Attack vector: Compromised extensions on OpenVSX / VS Code Marketplace
# Post-infection: Harvests npm, GitHub, Git, OpenVSX credentials
# Reference: https://www.truesec.com/hub/blog/glassworm-self-propagating-vscode-extension
#
# Usage: ./scripts/scan-extensions-glassworm.sh [extensions_dir]
# Default: ~/.vscode/extensions

set -euo pipefail

# Color output
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Determine extensions directory
EXTENSIONS_DIR="${1:-$HOME/.vscode/extensions}"

# Also check common alternative locations
ALT_DIRS=(
    "$HOME/.vscode-insiders/extensions"
    "$HOME/.cursor/extensions"
)

echo "=== GlassWorm Extension Scanner ==="
echo ""

# Bidi control characters (the actual GlassWorm payload mechanism)
# U+202A LEFT-TO-RIGHT EMBEDDING
# U+202B RIGHT-TO-LEFT EMBEDDING
# U+202C POP DIRECTIONAL FORMATTING
# U+202D LEFT-TO-RIGHT OVERRIDE
# U+202E RIGHT-TO-LEFT OVERRIDE
# U+2066 LEFT-TO-RIGHT ISOLATE
# U+2067 RIGHT-TO-LEFT ISOLATE
# U+2068 FIRST STRONG ISOLATE
# U+2069 POP DIRECTIONAL ISOLATE
# U+200F RIGHT-TO-LEFT MARK
# U+061C ARABIC LETTER MARK
# Zero-width characters
# U+200B ZERO WIDTH SPACE
# U+200C ZERO WIDTH NON-JOINER
# U+200D ZERO WIDTH JOINER
# U+FEFF ZERO WIDTH NO-BREAK SPACE (BOM)
#
# NOTE: Does NOT flag variation selectors (U+FE00-FE0F) — those are used by
# legitimate emojis and cause false positives.
PATTERN=$'[\xe2\x80\xab\xe2\x80\xac\xe2\x80\xad\xe2\x80\xae\xe2\x80\xaa\xe2\x81\xa6\xe2\x81\xa7\xe2\x81\xa8\xe2\x81\xa9\xe2\x80\x8f\xd8\x9c\xe2\x80\x8b\xe2\x80\x8c\xe2\x80\x8d\xef\xbb\xbf]'

FOUND=0
SCANNED=0
EXTENSIONS_SCANNED=0

scan_directory() {
    local dir="$1"
    local dir_name
    dir_name=$(basename "$(dirname "$dir")")

    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}SKIP${NC} $dir (not found)"
        return
    fi

    local ext_count
    ext_count=$(find "$dir" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
    echo "Scanning $dir ($ext_count extensions)..."
    echo ""

    for ext_dir in "$dir"/*/; do
        [ -d "$ext_dir" ] || continue
        local ext_name
        ext_name=$(basename "$ext_dir")
        EXTENSIONS_SCANNED=$((EXTENSIONS_SCANNED + 1))

        # Scan JS/TS/JSON files in the extension
        while IFS= read -r -d '' file; do
            SCANNED=$((SCANNED + 1))
            if grep -Pn "$PATTERN" "$file" 2>/dev/null; then
                echo -e "${RED}ALERT${NC} Invisible Unicode in: $ext_name"
                echo "  File: $file"
                echo ""
                FOUND=$((FOUND + 1))
            fi
        done < <(find "$ext_dir" -type f \( -name '*.js' -o -name '*.ts' -o -name '*.mjs' -o -name '*.cjs' -o -name '*.json' \) -not -path '*/node_modules/*' -print0 2>/dev/null)
    done
}

# Scan primary directory
scan_directory "$EXTENSIONS_DIR"

# Scan alternative directories if they exist
for alt_dir in "${ALT_DIRS[@]}"; do
    if [ -d "$alt_dir" ]; then
        scan_directory "$alt_dir"
    fi
done

echo "---"
echo "Extensions scanned: $EXTENSIONS_SCANNED"
echo "Files scanned: $SCANNED"

if [ "$FOUND" -gt 0 ]; then
    echo ""
    echo -e "${RED}FOUND $FOUND file(s) with invisible Unicode characters.${NC}"
    echo ""
    echo "Recommended actions:"
    echo "  1. Uninstall the flagged extension(s) immediately"
    echo "  2. Rotate npm tokens:  npm token revoke <token> && npm login"
    echo "  3. Rotate GitHub tokens: gh auth logout && gh auth login"
    echo "  4. Check git credentials: git credential reject"
    echo "  5. Review recent commits for unauthorized changes"
    exit 1
else
    echo -e "${GREEN}No invisible Unicode characters found. Extensions look clean.${NC}"
    exit 0
fi
