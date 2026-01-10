#!/bin/bash
# ============================================================
# Hook: pre-task-context.sh
# Event: PreToolUse (Task tool)
# Purpose: Advisory check for subagent context
# Session: 085
#
# Philosophy (Auftragstaktik):
#   Commanders decide what "kit" to provide. This hook
#   advises on sparse context but NEVER blocks - trust
#   the chain of command.
#
# Checks:
#   1. Identity card presence (BOOT CONTEXT)
#   2. Minimum context length
#   3. Capabilities reference
#
# Exit Codes:
#   0 - Always (advisory only, never blocks)
# ============================================================

# Read tool input from stdin
INPUT=$(cat)

# Extract the prompt parameter
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)

# If no prompt, allow (might be resume or other pattern)
if [ -z "$PROMPT" ]; then
    exit 0
fi

# Check 1: Identity card presence
if ! echo "$PROMPT" | grep -qiE "BOOT CONTEXT|identity|\.identity\.md"; then
    echo "ADVISORY: No identity card detected in Task spawn" >&2
    echo "Consider including: Read('.claude/Identities/[AGENT].identity.md')" >&2
fi

# Check 2: Minimum context length
WORD_COUNT=$(echo "$PROMPT" | wc -w | tr -d ' ')
if [ "$WORD_COUNT" -lt 30 ]; then
    echo "ADVISORY: Sparse context ($WORD_COUNT words) - subagent may need to self-discover" >&2
    echo "Subagent can read: .claude/Governance/CAPABILITIES.md" >&2
fi

# Check 3: Capabilities reference (info only)
if echo "$PROMPT" | grep -qi "CAPABILITIES.md"; then
    echo "INFO: Capabilities reference included - subagent can self-discover" >&2
fi

# Always allow - commander's discretion
exit 0
