#!/bin/bash
# Validates spawn chain consistency between identity cards and SPAWN_CHAINS.md
# Run: ./scripts/validate-spawn-chains.sh
#
# COMPATIBILITY: bash 3.2+ (macOS default)
# NOTE: Does NOT use associative arrays (bash 4.0+ feature) for portability

set -e
set -o pipefail

IDENTITIES_DIR=".claude/Identities"
SPAWN_CHAINS_FILE=".claude/Governance/SPAWN_CHAINS.md"
AGENTS_DIR=".claude/Agents"
ERRORS=0
WARNINGS=0

echo "Validating spawn chains..."
echo "========================================="
echo "Bash version: $BASH_VERSION"
echo ""

if [[ ! -f "$SPAWN_CHAINS_FILE" ]]; then
    echo "ERROR: SPAWN_CHAINS.md not found at $SPAWN_CHAINS_FILE"
    exit 1
fi

echo "## Phase 1: Validate spawnable agents exist"
echo ""

# Extract all agent names that appear in "Can Spawn" lines
for identity_file in "$IDENTITIES_DIR"/*.identity.md; do
    if [[ ! -f "$identity_file" ]]; then
        continue
    fi

    agent_name=$(basename "$identity_file" .identity.md)

    # Skip TEMPLATE
    [[ "$agent_name" == "TEMPLATE" ]] && continue

    # Extract "Can Spawn:" line
    spawn_line=$(grep "Can Spawn:" "$identity_file" 2>/dev/null | head -1 || echo "")

    if [[ -z "$spawn_line" ]]; then
        continue
    fi

    # Extract agents from spawn line (after the colon)
    # Split by comma, trim leading/trailing spaces, filter out descriptive phrases
    # First remove all parenthetical content, then split and filter
    spawn_list=$(echo "$spawn_line" | sed 's/.*Can Spawn://' | sed 's/([^)]*)//g' | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v "^$" | grep -v "^None$" | grep -v "task-specific" | grep -v "agents as needed" | grep -v "wide lateral" | grep -v "^\[" || true)

    invalid_spawns=""
    # Use while read to avoid glob expansion issues
    echo "$spawn_list" | while IFS= read -r spawnable; do
        # Clean up the name (remove asterisks, parenthetical notes, markdown bold)
        clean_name=$(echo "$spawnable" | sed 's/\*//g' | sed 's/(.*)//' | tr -d ' ')

        if [[ -z "$clean_name" ]]; then
            continue
        fi

        # Skip descriptive phrases, None, skills (start with /), and template placeholders
        case "$clean_name" in
            ANY|ANYagent|None|task-specific|agents|as|needed|through|ranges|intel|specialists|uses|for|process|wide|lateral|authority|IG|HISTORIAN)
                continue
                ;;
            /*)  # Skip skill references like /search-party
                continue
                ;;
            \[*)  # Skip template placeholders like [Comma-separated
                continue
                ;;
            *\]*)  # Skip template placeholders like "None"]
                continue
                ;;
        esac

        # Check if this agent exists (either as identity or agent spec)
        identity_exists="$IDENTITIES_DIR/${clean_name}.identity.md"
        agent_exists="$AGENTS_DIR/${clean_name}.md"

        if [[ ! -f "$identity_exists" && ! -f "$agent_exists" ]]; then
            echo "   WARNING: $agent_name references non-existent agent: $clean_name" >&2
        fi
    done

    echo "   $agent_name"
done

echo ""
echo "## Phase 2: Validate chain of command consistency"
echo ""

# Check that "Reports To" references valid agents
for identity_file in "$IDENTITIES_DIR"/*.identity.md; do
    if [[ ! -f "$identity_file" ]]; then
        continue
    fi

    agent_name=$(basename "$identity_file" .identity.md)

    # Skip TEMPLATE
    [[ "$agent_name" == "TEMPLATE" ]] && continue

    # Extract "Reports To:" line
    reports_line=$(grep "Reports To:" "$identity_file" 2>/dev/null | head -1 || echo "")

    if [[ -z "$reports_line" ]]; then
        echo "   MISSING: $agent_name has no 'Reports To' field"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # Extract the parent agent name (strip markdown bold markers **)
    parent=$(echo "$reports_line" | sed 's/.*Reports To://' | tr -d ' ' | sed 's/\*\*//g' | sed 's/(.*)//' | cut -d',' -f1)

    # Special cases
    case "$parent" in
        ORCHESTRATOR|User-InvokedOnly|Independent|UserInvocation)
            echo "   $agent_name -> $parent"
            continue
            ;;
    esac

    # Check parent exists
    parent_identity="$IDENTITIES_DIR/${parent}.identity.md"
    parent_agent="$AGENTS_DIR/${parent}.md"

    if [[ -f "$parent_identity" || -f "$parent_agent" ]]; then
        echo "   $agent_name -> $parent"
    else
        echo "   BROKEN: $agent_name reports to non-existent $parent"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "## Phase 3: Deputy/Coordinator tier validation"
echo ""

# Validate tier structure from identity cards
for identity_file in "$IDENTITIES_DIR"/*.identity.md; do
    if [[ ! -f "$identity_file" ]]; then
        continue
    fi

    agent_name=$(basename "$identity_file" .identity.md)

    # Skip TEMPLATE and DELEGATION_AUDITOR (reference docs)
    [[ "$agent_name" == "TEMPLATE" || "$agent_name" == "DELEGATION_AUDITOR" ]] && continue

    # Extract Tier (strip markdown bold markers **)
    tier=$(grep -E "Tier:" "$identity_file" 2>/dev/null | head -1 | sed 's/.*Tier://' | sed 's/\*\*//g' | tr -d ' ' || echo "unknown")

    # Check tier makes sense based on naming
    case "$agent_name" in
        ARCHITECT|SYNTHESIZER|USASOC)
            if [[ "$tier" != "Deputy" ]]; then
                echo "   MISMATCH: $agent_name should be Deputy tier (found: $tier)"
                WARNINGS=$((WARNINGS + 1))
            else
                echo "   $agent_name: Deputy"
            fi
            ;;
        COORD_*)
            if [[ "$tier" != "Coordinator" ]]; then
                echo "   MISMATCH: $agent_name should be Coordinator tier (found: $tier)"
                WARNINGS=$((WARNINGS + 1))
            else
                echo "   $agent_name: Coordinator"
            fi
            ;;
        G[1-6]_PERSONNEL|G[1-6]_RECON|G[1-6]_OPERATIONS|G[1-6]_CONTEXT_MANAGER|G[1-6]_PLANNING|G[1-6]_SIGNAL)
            # Only validate primary G-Staff agents, not their specialists (G4_LIBRARIAN, G4_SCRIPT_KIDDY)
            if [[ "$tier" != "G-Staff" ]]; then
                echo "   MISMATCH: $agent_name should be G-Staff tier (found: $tier)"
                WARNINGS=$((WARNINGS + 1))
            else
                echo "   $agent_name: G-Staff"
            fi
            ;;
        18[A-Z]_*)
            if [[ "$tier" != "SOF" ]]; then
                echo "   MISMATCH: $agent_name should be SOF tier (found: $tier)"
                WARNINGS=$((WARNINGS + 1))
            else
                echo "   $agent_name: SOF"
            fi
            ;;
    esac
done

echo ""
echo "## Summary"
echo ""

echo "========================================="
if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
    echo "All spawn chains validated successfully"
    exit 0
elif [[ $ERRORS -eq 0 ]]; then
    echo "Validation passed with $WARNINGS warning(s)"
    exit 0
else
    echo "Found $ERRORS error(s) and $WARNINGS warning(s)"
    exit 1
fi
