#!/bin/bash
# Validates that all agents have identity cards with required fields
# Run: ./scripts/validate-identity-cards.sh
#
# COMPATIBILITY: bash 3.2+ (macOS default)
# NOTE: Does NOT use associative arrays (bash 4.0+ feature) for portability

set -e

AGENTS_DIR=".claude/Agents"
IDENTITIES_DIR=".claude/Identities"
ERRORS=0
WARNINGS=0

echo "Validating identity cards..."
echo "========================================="
echo "Bash version: $BASH_VERSION"
echo ""

# Required fields in identity cards
REQUIRED_FIELDS="Role:|Chain of Command|Reports To:|Can Spawn:|Standing Orders|Escalation Triggers|Key Constraints"

# Agents that don't need identity cards (not spawned, or reference docs)
is_exempt() {
    case "$1" in
        ORCHESTRATOR)       return 0 ;;  # Top-level, never spawned
        STANDARD_OPERATIONS) return 0 ;; # Reference doc, not agent
        DELEGATION_AUDITOR) return 0 ;;  # Reference doc
        TEMPLATE)           return 0 ;;  # Template file, not agent
        *)                  return 1 ;;
    esac
}

echo "## Phase 1: Check agents have identity cards"
echo ""

# Check each agent spec has an identity card
for agent_file in "$AGENTS_DIR"/*.md; do
    if [[ ! -f "$agent_file" ]]; then
        continue
    fi

    agent_name=$(basename "$agent_file" .md)
    identity_file="$IDENTITIES_DIR/${agent_name}.identity.md"

    if is_exempt "$agent_name"; then
        echo "   EXEMPT: $agent_name (not spawned)"
        continue
    fi

    if [[ -f "$identity_file" ]]; then
        echo "   $agent_name"
    else
        echo "   MISSING: $agent_name (no identity card)"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "## Phase 2: Validate identity card structure"
echo ""

# Check each identity card has required fields
for identity_file in "$IDENTITIES_DIR"/*.identity.md; do
    if [[ ! -f "$identity_file" ]]; then
        continue
    fi

    agent_name=$(basename "$identity_file" .identity.md)
    missing_fields=""

    # Check for Role
    if ! grep -q "Role:" "$identity_file" 2>/dev/null; then
        missing_fields="$missing_fields Role"
    fi

    # Check for Reports To
    if ! grep -q "Reports To:" "$identity_file" 2>/dev/null; then
        missing_fields="$missing_fields ReportsTo"
    fi

    # Check for Can Spawn
    if ! grep -q "Can Spawn:" "$identity_file" 2>/dev/null; then
        missing_fields="$missing_fields CanSpawn"
    fi

    # Check for Standing Orders
    if ! grep -q "Standing Orders" "$identity_file" 2>/dev/null; then
        missing_fields="$missing_fields StandingOrders"
    fi

    # Check for Key Constraints
    if ! grep -q "Key Constraints" "$identity_file" 2>/dev/null; then
        missing_fields="$missing_fields KeyConstraints"
    fi

    if [[ -z "$missing_fields" ]]; then
        echo "   $agent_name"
    else
        echo "   INCOMPLETE: $agent_name (missing:$missing_fields)"
        WARNINGS=$((WARNINGS + 1))
    fi
done

echo ""
echo "## Phase 3: Check for orphan identity cards"
echo ""

# Check for identity cards without agent specs
for identity_file in "$IDENTITIES_DIR"/*.identity.md; do
    if [[ ! -f "$identity_file" ]]; then
        continue
    fi

    agent_name=$(basename "$identity_file" .identity.md)
    agent_file="$AGENTS_DIR/${agent_name}.md"

    if [[ -f "$agent_file" ]]; then
        continue  # Has matching agent spec
    fi

    # Check if it's an exempt agent (may not have full spec)
    if is_exempt "$agent_name"; then
        continue
    fi

    echo "   ORPHAN: $agent_name (identity card without agent spec)"
    WARNINGS=$((WARNINGS + 1))
done

if [[ $WARNINGS -eq 0 ]]; then
    echo "   No orphans found"
fi

echo ""
echo "## Summary"
echo ""

# Count totals
AGENT_COUNT=$(ls -1 "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
IDENTITY_COUNT=$(ls -1 "$IDENTITIES_DIR"/*.identity.md 2>/dev/null | wc -l | tr -d ' ')

echo "Agent specs:     $AGENT_COUNT"
echo "Identity cards:  $IDENTITY_COUNT"
echo ""

echo "========================================="
if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
    echo "All identity cards validated successfully"
    exit 0
elif [[ $ERRORS -eq 0 ]]; then
    echo "Validation passed with $WARNINGS warning(s)"
    exit 0
else
    echo "Found $ERRORS error(s) and $WARNINGS warning(s)"
    exit 1
fi
