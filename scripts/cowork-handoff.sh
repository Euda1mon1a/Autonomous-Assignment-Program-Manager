#!/bin/bash
# cowork-handoff.sh - Prepare workspace folder for Claude Cowork
#
# Usage: ./scripts/cowork-handoff.sh <domain> <task-name> [context-files...]
#
# Domains: research, presentations, exports, drafts
#
# Examples:
#   ./scripts/cowork-handoff.sh research irb-submission
#   ./scripts/cowork-handoff.sh presentations quarterly-review docs/roadmap.md
#   ./scripts/cowork-handoff.sh research wellness-study docs/features/GAMIFIED_RESEARCH_PLATFORM.md backend/app/schemas/wellness.py

set -e

WORKSPACE_ROOT="$(cd "$(dirname "$0")/.." && pwd)/workspace"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Validate arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo ""
    echo "Usage: $0 <domain> <task-name> [context-files...]"
    echo ""
    echo "Domains: research, presentations, exports, drafts"
    echo ""
    echo "Examples:"
    echo "  $0 research irb-submission"
    echo "  $0 presentations quarterly-review docs/roadmap.md"
    exit 1
fi

DOMAIN="$1"
TASK_NAME="$2"
shift 2
CONTEXT_FILES=("$@")

# Validate domain
case "$DOMAIN" in
    research|presentations|exports|drafts)
        ;;
    *)
        echo -e "${RED}Error: Invalid domain '$DOMAIN'${NC}"
        echo "Valid domains: research, presentations, exports, drafts"
        exit 1
        ;;
esac

# Create task folder
TASK_FOLDER="$WORKSPACE_ROOT/$DOMAIN/$TASK_NAME"
mkdir -p "$TASK_FOLDER"

echo -e "${CYAN}Creating Cowork handoff folder...${NC}"
echo ""

# Copy context files
if [ ${#CONTEXT_FILES[@]} -gt 0 ]; then
    echo -e "${YELLOW}Copying context files:${NC}"
    for file in "${CONTEXT_FILES[@]}"; do
        if [ -f "$file" ]; then
            # Get filename and extension
            filename=$(basename "$file")
            # Copy with CONTEXT_ prefix
            cp "$file" "$TASK_FOLDER/CONTEXT_$filename"
            echo "  - $file -> CONTEXT_$filename"
        else
            echo -e "${RED}  - Warning: $file not found, skipping${NC}"
        fi
    done
    echo ""
fi

# Generate task brief
TASK_FILE="$TASK_FOLDER/TASK_${TASK_NAME}.md"

# Build context files table
CONTEXT_TABLE=""
for file in "$TASK_FOLDER"/CONTEXT_*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        CONTEXT_TABLE="$CONTEXT_TABLE| \`$filename\` | Copied context |\n"
    fi
done

# Domain-specific deliverables
case "$DOMAIN" in
    research)
        DELIVERABLES="### 1. Protocol Document
- Study objectives and methodology
- Participant criteria
- Data collection procedures

### 2. Consent Form
- Plain language description
- Voluntary participation statement
- Privacy protections

### 3. Data Management Plan
- Storage and security
- Retention period
- De-identification protocol"
        ;;
    presentations)
        DELIVERABLES="### 1. Slide Deck
- Executive summary
- Key metrics and achievements
- Roadmap and next steps

### 2. Speaker Notes
- Talking points for each slide
- Q&A preparation"
        ;;
    exports)
        DELIVERABLES="### 1. Report Document
- Summary findings
- Data tables
- Recommendations"
        ;;
    drafts)
        DELIVERABLES="### 1. Draft Document
- [Specify deliverables based on task]"
        ;;
esac

cat > "$TASK_FILE" << EOF
# Task: ${TASK_NAME//-/ }

## Objective

[Describe the objective for this ${DOMAIN} task]

## Context Files (in this folder)

| File | Contents |
|------|----------|
$(echo -e "$CONTEXT_TABLE")

## Deliverables

Create the following documents in this folder:

$DELIVERABLES

## Key Facts

- Domain: $DOMAIN
- Task: $TASK_NAME
- [Add relevant facts from context files]

## Style Notes

- Prefer Markdown format (converts easily to Word/PDF)
- Use formal language for research, bullet points for presentations
- Reference context files but don't duplicate code
EOF

echo -e "${GREEN}Task brief created: TASK_${TASK_NAME}.md${NC}"
echo ""

# Output summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Cowork handoff folder ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Folder path for Cowork access:"
echo -e "${CYAN}$TASK_FOLDER${NC}"
echo ""
echo "Contents:"
ls -la "$TASK_FOLDER"
echo ""
echo -e "${YELLOW}Next step: Give Cowork access to this folder${NC}"
