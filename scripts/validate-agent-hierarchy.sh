#!/bin/bash
# Validates that agent specs match HIERARCHY.md reporting structure
# Run: ./scripts/validate-agent-hierarchy.sh

set -e

AGENTS_DIR=".claude/Agents"
HIERARCHY_FILE=".claude/Governance/HIERARCHY.md"
ERRORS=0

echo "Validating agent hierarchy consistency..."
echo "========================================="

# Expected reporting structure (from HIERARCHY.md)
declare -A EXPECTED_REPORTS
EXPECTED_REPORTS["G1_PERSONNEL"]="SYNTHESIZER"
EXPECTED_REPORTS["G2_RECON"]="ORCHESTRATOR"
EXPECTED_REPORTS["G3_OPERATIONS"]="SYNTHESIZER"
EXPECTED_REPORTS["G4_CONTEXT_MANAGER"]="SYNTHESIZER"
EXPECTED_REPORTS["G5_PLANNING"]="ORCHESTRATOR"
EXPECTED_REPORTS["G6_SIGNAL"]="ARCHITECT"

# Check each G-Staff agent
for agent in "${!EXPECTED_REPORTS[@]}"; do
    expected="${EXPECTED_REPORTS[$agent]}"
    file="$AGENTS_DIR/${agent}.md"

    if [[ ! -f "$file" ]]; then
        echo "❌ MISSING: $file"
        ((ERRORS++))
        continue
    fi

    # Extract "Reports To" line (line 8 typically)
    reports_to=$(grep -i "Reports To:" "$file" | head -1 || echo "")

    if [[ -z "$reports_to" ]]; then
        echo "❌ NO REPORTS TO: $agent"
        ((ERRORS++))
        continue
    fi

    if [[ "$reports_to" == *"$expected"* ]]; then
        echo "✅ $agent → $expected"
    else
        echo "❌ MISMATCH: $agent"
        echo "   Expected: $expected"
        echo "   Found: $reports_to"
        ((ERRORS++))
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
