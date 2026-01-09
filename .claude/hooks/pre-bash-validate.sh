#!/bin/bash
# Pre-Bash Validation Hook - Command Safety Check
# Validates bash commands before execution

# Read the tool input from stdin (JSON format)
INPUT=$(cat)

# Extract the command being run
# Claude Code passes: { "tool_input": { "command": "..." } }
if command -v jq &> /dev/null; then
    COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || echo "")
else
    # Fallback: fragile grep parsing
    COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"command"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//' || echo "")
fi

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.antigravity/logs/bash-commands.log"

log() {
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $1" >> "$LOG_FILE" 2>/dev/null || true
}

# Log the command
log "CMD: $COMMAND"

# Blocked patterns (exit code 2 = blocking error)
BLOCKED_PATTERNS=(
    "git push --force"
    "git push -f"
    "git reset --hard"
    "rm -rf /"
    "rm -rf ~"
    "DROP DATABASE"
    "DROP TABLE"
    "TRUNCATE"
    "> /dev/sd"
    "mkfs"
    "dd if="
    ":(){:|:&};:"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qi "$pattern"; then
        log "BLOCKED: $COMMAND (matched: $pattern)"
        echo "Blocked: Command matches dangerous pattern '$pattern'" >&2
        exit 2
    fi
done

# Warning patterns (log but allow)
# Note: Patterns use extended regex (-E flag in grep)
WARNING_PATTERNS=(
    "^sudo "
    "chmod 777"
    "curl .* \| .*sh"
    "wget .* \| .*sh"
)

for pattern in "${WARNING_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
        log "WARNING: $COMMAND (matched: $pattern)"
    fi
done

# Special check: git push without remote tracking
if echo "$COMMAND" | grep -qE "^git push|git push "; then
    CURRENT_BRANCH=$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || echo "")
    if [ -n "$CURRENT_BRANCH" ]; then
        UPSTREAM=$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")
        if [ -z "$UPSTREAM" ]; then
            # Check if -u flag is present (setting up tracking)
            if ! echo "$COMMAND" | grep -qE "\-u |--set-upstream"; then
                echo "" >&2
                echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" >&2
                echo "  WARNING: Branch '$CURRENT_BRANCH' has no remote!" >&2
                echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" >&2
                echo "" >&2
                echo "  Use: git push -u origin $CURRENT_BRANCH" >&2
                echo "" >&2
                log "WARNING: git push on untracked branch $CURRENT_BRANCH"
            fi
        fi
    fi
fi

# Special check: git commit on main/master
if echo "$COMMAND" | grep -qE "^git commit|git commit "; then
    CURRENT_BRANCH=$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || echo "")
    if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
        echo "" >&2
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" >&2
        echo "  WARNING: Committing directly to $CURRENT_BRANCH!" >&2
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" >&2
        echo "" >&2
        echo "  Consider creating a feature branch first." >&2
        echo "" >&2
        log "WARNING: git commit on $CURRENT_BRANCH"
    fi
fi

# Command approved
exit 0
