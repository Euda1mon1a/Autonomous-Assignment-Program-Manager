#!/bin/bash
# ============================================================
# Hook: post-metrics-collect.sh
# Purpose: PostToolUse hook for session metrics collection
# Domain: G6_SIGNAL Advisory
# Event: PostToolUse (all tools)
# Session: 082
#
# Metrics Collected:
#   - Command execution counts by tool
#   - Error rates
#   - Session activity timestamps
#   - Tool usage patterns
#
# Philosophy (Auftragstaktik):
#   Observe, don't obstruct. Metrics inform decisions.
#   Never block operations for metrics collection.
#
# Exit Codes:
#   0 - Always (metrics are non-blocking)
# ============================================================

INPUT=$(cat)

# Extract tool and result info
if command -v jq &> /dev/null; then
    TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"' 2>/dev/null || echo "unknown")
    TOOL_RESULT=$(echo "$INPUT" | jq -r '.tool_result.is_error // false' 2>/dev/null || echo "false")
else
    TOOL_NAME="unknown"
    TOOL_RESULT="false"
fi

# Metrics log location
METRICS_DIR="${HOME}/.claude/metrics"
METRICS_FILE="${METRICS_DIR}/session_metrics.jsonl"

# Ensure metrics directory exists
mkdir -p "$METRICS_DIR" 2>/dev/null || true

# Timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SESSION_DATE=$(date +"%Y-%m-%d")

# Log metric entry (JSON Lines format)
cat >> "$METRICS_FILE" 2>/dev/null <<EOF || true
{"timestamp":"$TIMESTAMP","date":"$SESSION_DATE","tool":"$TOOL_NAME","is_error":$TOOL_RESULT}
EOF

# Rotate log if too large (>10MB)
if [ -f "$METRICS_FILE" ]; then
    FILE_SIZE=$(stat -f%z "$METRICS_FILE" 2>/dev/null || stat -c%s "$METRICS_FILE" 2>/dev/null || echo "0")
    if [ "$FILE_SIZE" -gt 10485760 ]; then
        mv "$METRICS_FILE" "${METRICS_FILE}.$(date +%Y%m%d)" 2>/dev/null || true
    fi
fi

# Never block - always exit 0
exit 0
