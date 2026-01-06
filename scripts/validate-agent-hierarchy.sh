#!/bin/bash
# Validates that agent specs match HIERARCHY.md reporting structure
# Run: ./scripts/validate-agent-hierarchy.sh
#
# COMPATIBILITY: bash 3.2+ (macOS default)
# NOTE: Does NOT use associative arrays (bash 4.0+ feature) for portability

set -e

AGENTS_DIR=".claude/Agents"
HIERARCHY_FILE=".claude/Governance/HIERARCHY.md"
ERRORS=0

echo "Validating agent hierarchy consistency..."
echo "========================================="
echo "Bash version: $BASH_VERSION"
echo ""

# Expected reporting structure (from HIERARCHY.md)
# Using function instead of associative array for bash 3.2 compatibility
get_expected_report() {
    case "$1" in
        G1_PERSONNEL)       echo "SYNTHESIZER" ;;
        G2_RECON)           echo "ORCHESTRATOR" ;;
        G3_OPERATIONS)      echo "SYNTHESIZER" ;;
        G4_CONTEXT_MANAGER) echo "SYNTHESIZER" ;;
        G5_PLANNING)        echo "ORCHESTRATOR" ;;
        G6_SIGNAL)          echo "ARCHITECT" ;;
        *)                  echo "" ;;
    esac
}

# G-Staff agents to validate
AGENTS="G1_PERSONNEL G2_RECON G3_OPERATIONS G4_CONTEXT_MANAGER G5_PLANNING G6_SIGNAL"

# Check each G-Staff agent
for agent in $AGENTS; do
    expected=$(get_expected_report "$agent")
    file="$AGENTS_DIR/${agent}.md"

    if [[ ! -f "$file" ]]; then
        echo "❌ MISSING: $file"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # Extract "Reports To" line
    reports_to=$(grep -i "Reports To:" "$file" | head -1 || echo "")

    if [[ -z "$reports_to" ]]; then
        echo "❌ NO REPORTS TO: $agent"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    if [[ "$reports_to" == *"$expected"* ]]; then
        echo "✅ $agent → $expected"
    else
        echo "❌ MISMATCH: $agent"
        echo "   Expected: $expected"
        echo "   Found: $reports_to"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "========================================="
if [[ $ERRORS -eq 0 ]]; then
    echo "✅ All agents validated successfully"
    exit 0
else
    echo "❌ Found $ERRORS error(s)"
    exit 1
fi
