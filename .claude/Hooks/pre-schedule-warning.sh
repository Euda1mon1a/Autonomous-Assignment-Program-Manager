#!/bin/bash
# Pre-Edit Schedule Warning Hook
# Reminds to run validation tools before editing schedule-related code

# Read the tool input from stdin (JSON format)
INPUT=$(cat)

# Extract the file path being edited
# Claude Code passes: { "tool_input": { "file_path": "..." } }
if command -v jq &> /dev/null; then
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")
else
    # Fallback: fragile grep parsing
    FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"file_path"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//' || echo "")
fi

# Only warn for schedule-related files
# Patterns that indicate scheduling code
SCHEDULE_PATTERNS=(
    "/scheduling/"
    "/schedule/"
    "schedule_"
    "_schedule"
    "acgme_"
    "constraint"
    "swap"
)

IS_SCHEDULE_FILE=false
for pattern in "${SCHEDULE_PATTERNS[@]}"; do
    if echo "$FILE_PATH" | grep -qi "$pattern"; then
        IS_SCHEDULE_FILE=true
        break
    fi
done

# If editing schedule code, show a reminder
if [ "$IS_SCHEDULE_FILE" = true ]; then
    echo "" >&2
    echo "================================================================" >&2
    echo "  SCHEDULING CODE DETECTED: $FILE_PATH" >&2
    echo "================================================================" >&2
    echo "" >&2
    echo "  BEFORE making changes, have you run these MCP tools?" >&2
    echo "" >&2
    echo "  1. validate_schedule_tool - Check for existing violations" >&2
    echo "  2. get_defense_level_tool - Check current resilience" >&2
    echo "  3. rag_search(\"[topic]\") - Query knowledge base" >&2
    echo "" >&2
    echo "  These tools prevent ACGME violations and operational failures." >&2
    echo "================================================================" >&2
    echo "" >&2
fi

# Always allow the edit (this is just a warning, not a blocker)
exit 0
