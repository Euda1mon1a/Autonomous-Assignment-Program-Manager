#!/bin/bash
# =============================================================================
# Generate Diagram Bundle
# =============================================================================
# Extracts all mermaid diagrams from docs/ into a consolidated bundle
# for efficient AI context preloading.
#
# Usage:
#   ./scripts/generate-diagram-bundle.sh
#   ./scripts/generate-diagram-bundle.sh --check  # Check if bundle is stale
#
# Output:
#   docs/rag-knowledge/DIAGRAM_BUNDLE.md
# =============================================================================

set -e

OUTPUT="docs/rag-knowledge/DIAGRAM_BUNDLE.md"
TEMP_OUTPUT=$(mktemp)
CHECK_MODE=false

if [[ "$1" == "--check" ]]; then
    CHECK_MODE=true
fi

# Find all files with mermaid diagrams
DIAGRAM_FILES=$(grep -rl '```mermaid' docs/ 2>/dev/null | grep -v DIAGRAM_BUNDLE.md | sort)
DIAGRAM_COUNT=$(echo "$DIAGRAM_FILES" | grep -c . || echo "0")

echo "Found $DIAGRAM_COUNT files with mermaid diagrams"

# Generate header
cat > "$TEMP_OUTPUT" << 'HEADER'
# Architecture Diagram Bundle

> **Purpose:** Consolidated mermaid diagrams for AI context preloading
> **Auto-generated:** Do not edit manually - run `scripts/generate-diagram-bundle.sh`
> **doc_type:** architecture_diagrams

This bundle contains all architecture diagrams extracted from the codebase for efficient AI context loading. Each diagram is machine-readable mermaid syntax with source attribution.

---

## Quick Stats

HEADER

# Add stats
echo "- **Files scanned:** $DIAGRAM_COUNT" >> "$TEMP_OUTPUT"
TOTAL_DIAGRAMS=$(grep -rh '```mermaid' docs/ 2>/dev/null | grep -v DIAGRAM_BUNDLE.md | wc -l | tr -d ' ')
echo "- **Total diagrams:** $TOTAL_DIAGRAMS" >> "$TEMP_OUTPUT"
echo "- **Generated:** $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$TEMP_OUTPUT"
echo "" >> "$TEMP_OUTPUT"
echo "---" >> "$TEMP_OUTPUT"
echo "" >> "$TEMP_OUTPUT"

# Process each file
for file in $DIAGRAM_FILES; do
    if [[ -f "$file" ]]; then
        # Get relative path
        rel_path="${file#./}"

        # Get filename without extension for section header
        filename=$(basename "$file" .md)

        # Count diagrams in this file
        file_diagram_count=$(grep -c '```mermaid' "$file" || echo "0")

        echo "## $filename" >> "$TEMP_OUTPUT"
        echo "" >> "$TEMP_OUTPUT"
        echo "**Source:** \`$rel_path\`" >> "$TEMP_OUTPUT"
        echo "**Diagrams:** $file_diagram_count" >> "$TEMP_OUTPUT"
        echo "" >> "$TEMP_OUTPUT"

        # Extract mermaid blocks with context
        # Use awk to extract ```mermaid blocks
        awk '
            /```mermaid/ {
                in_block=1
                print ""
                print "```mermaid"
                next
            }
            /```/ && in_block {
                print "```"
                print ""
                in_block=0
                next
            }
            in_block { print }
        ' "$file" >> "$TEMP_OUTPUT"

        echo "---" >> "$TEMP_OUTPUT"
        echo "" >> "$TEMP_OUTPUT"
    fi
done

# Add footer
cat >> "$TEMP_OUTPUT" << 'FOOTER'
## Regeneration

To regenerate this bundle:

```bash
./scripts/generate-diagram-bundle.sh
```

To check if bundle is stale:

```bash
./scripts/generate-diagram-bundle.sh --check
```

---

*This file is auto-generated. Do not edit manually.*
FOOTER

if $CHECK_MODE; then
    # Check mode: compare with existing
    if [[ -f "$OUTPUT" ]]; then
        # Compare ignoring timestamps
        EXISTING_HASH=$(grep -v "Generated:" "$OUTPUT" | md5sum | cut -d' ' -f1)
        NEW_HASH=$(grep -v "Generated:" "$TEMP_OUTPUT" | md5sum | cut -d' ' -f1)

        if [[ "$EXISTING_HASH" != "$NEW_HASH" ]]; then
            echo "STALE: Diagram bundle needs regeneration"
            echo "Run: ./scripts/generate-diagram-bundle.sh"
            rm "$TEMP_OUTPUT"
            exit 1
        else
            echo "OK: Diagram bundle is up to date"
            rm "$TEMP_OUTPUT"
            exit 0
        fi
    else
        echo "MISSING: Diagram bundle does not exist"
        rm "$TEMP_OUTPUT"
        exit 1
    fi
else
    # Generate mode: write output
    mv "$TEMP_OUTPUT" "$OUTPUT"
    echo "Generated: $OUTPUT"
    echo "Diagrams: $TOTAL_DIAGRAMS from $DIAGRAM_COUNT files"
fi
