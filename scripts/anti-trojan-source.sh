#!/usr/bin/env bash
# GlassWorm / Trojan Source defense
# Detects invisible Unicode characters that can hide malicious code:
# - Bidi control characters (U+202A-202E, U+2066-2069, U+200F, U+061C)
# - Zero-width characters (U+200B-U+200D, U+FEFF)
# - Variation selectors (U+FE00-U+FE0F)
#
# Scans staged files only. Returns non-zero if dangerous characters found.

set -euo pipefail

# Get staged files (filter to code files)
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|ts|tsx|js|jsx|sh|md)$' || true)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

FOUND=0

# Unicode ranges to detect (hex codepoints)
# Bidi controls: U+202A-202E, U+2066-2069, U+200F, U+061C
# Zero-width: U+200B-U+200D, U+FEFF
# Variation selectors: U+FE00-U+FE0F
PATTERN=$'[\xe2\x80\xab\xe2\x80\xac\xe2\x80\xad\xe2\x80\xae\xe2\x80\xaa\xe2\x81\xa6\xe2\x81\xa7\xe2\x81\xa8\xe2\x81\xa9\xe2\x80\x8f\xd8\x9c\xe2\x80\x8b\xe2\x80\x8c\xe2\x80\x8d\xef\xbb\xbf]'

for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        if grep -Pn "$PATTERN" "$file" 2>/dev/null; then
            echo "::error::Invisible Unicode character detected in $file"
            FOUND=1
        fi
    fi
done

if [ "$FOUND" -eq 1 ]; then
    echo ""
    echo "ERROR: Invisible Unicode characters detected (potential Trojan Source / GlassWorm attack)."
    echo "Remove these characters before committing."
    exit 1
fi

exit 0
