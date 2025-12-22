***REMOVED***!/bin/bash
***REMOVED*** Pre-Bash Validation Hook - Command Safety Check
***REMOVED*** Validates bash commands before execution

***REMOVED*** Read the tool input from stdin (JSON format)
INPUT=$(cat)

***REMOVED*** Extract the command being run
COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"command"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//' || echo "")

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.antigravity/logs/bash-commands.log"

log() {
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $1" >> "$LOG_FILE" 2>/dev/null || true
}

***REMOVED*** Log the command
log "CMD: $COMMAND"

***REMOVED*** Blocked patterns (exit code 2 = blocking error)
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

***REMOVED*** Warning patterns (log but allow)
WARNING_PATTERNS=(
    "sudo"
    "chmod 777"
    "curl.*|.*sh"
    "wget.*|.*sh"
)

for pattern in "${WARNING_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
        log "WARNING: $COMMAND (matched: $pattern)"
    fi
done

***REMOVED*** Command approved
exit 0
