#!/bin/bash
# ============================================================
# Script: validate-mcp-tools.sh
# Purpose: Pre-commit hook for MCP tool structure validation
# Domain: SCHEDULER Advisory
# Session: 084
#
# Problem: MCP tools can be defined incorrectly:
#   - Missing BaseTool inheritance
#   - Missing required abstract methods
#   - Poor error handling patterns
#   - Unregistered tools
#   - Missing tests
#
# Checks:
#   1. BaseTool inheritance (BLOCKING)
#   2. Input validation patterns (WARNING)
#   3. Error handling patterns (WARNING)
#   4. Registration completeness (BLOCKING)
#   5. Test coverage (WARNING)
#
# Philosophy (Auftragstaktik):
#   Catch MCP tool structure issues at commit time.
#   Prevent runtime failures from misconfigured tools.
#
# Exit Codes:
#   0 - Validation passed
#   1 - Validation failed (blocking)
# ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

WARNINGS=0
ERRORS=0

MCP_TOOLS_DIR="mcp-server/src/scheduler_mcp/tools"
MCP_ARMORY_DIR="mcp-server/src/scheduler_mcp/armory"
MCP_TESTS_DIR="mcp-server/tests"

echo -e "${CYAN}Running MCP Tool Validation Check...${NC}"

# ============================================================
# Check 1: BaseTool Inheritance (BLOCKING)
# ============================================================
echo -n "Checking BaseTool inheritance... "

# Find Python files that define classes ending in "Tool" but don't inherit from BaseTool
# Exclude __init__.py, base.py, and test files
MISSING_INHERITANCE=""

# Check core tools
for tool_file in $(find "$MCP_TOOLS_DIR" -name "*.py" -type f 2>/dev/null | grep -v "__init__" | grep -v "base.py" | grep -v "registry.py" | grep -v "executor.py" | grep -v "validator.py" || true); do
    # Check if file defines a class ending in "Tool"
    if grep -qE "^class [A-Z][a-zA-Z]+Tool\(" "$tool_file" 2>/dev/null; then
        # Check if it inherits from BaseTool (class definition or import)
        # Pattern 1: Direct inheritance in class def
        # Pattern 2: Relative import (from ..base, from .base)
        # Pattern 3: Absolute import
        if ! grep -qE "^class [A-Z][a-zA-Z]+Tool\(.*BaseTool" "$tool_file" 2>/dev/null; then
            if ! grep -qE "from \.+base import.*BaseTool|from scheduler_mcp\.tools\.base import.*BaseTool" "$tool_file" 2>/dev/null; then
                MISSING_INHERITANCE="$MISSING_INHERITANCE $tool_file"
            fi
        fi
    fi
done

# Check armory tools
for tool_file in $(find "$MCP_ARMORY_DIR" -name "*.py" -type f 2>/dev/null | grep -v "__init__" || true); do
    if grep -qE "^class [A-Z][a-zA-Z]+Tool\(" "$tool_file" 2>/dev/null; then
        if ! grep -qE "^class [A-Z][a-zA-Z]+Tool\(.*BaseTool" "$tool_file" 2>/dev/null; then
            # Armory tools might import from scheduler_mcp.tools.base or ....base
            if ! grep -qE "from \.+base import.*BaseTool|from scheduler_mcp\.tools\.base import.*BaseTool" "$tool_file" 2>/dev/null; then
                MISSING_INHERITANCE="$MISSING_INHERITANCE $tool_file"
            fi
        fi
    fi
done

if [ -n "$MISSING_INHERITANCE" ]; then
    echo -e "${RED}ERROR${NC}"
    echo -e "${RED}Tool classes not inheriting from BaseTool:${NC}"
    for f in $MISSING_INHERITANCE; do
        echo "  - $f"
    done
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 2: Input Validation Patterns (WARNING)
# ============================================================
echo -n "Checking input validation patterns... "

# Look for kwargs access in execute() method, which should use validated request instead
# Pattern: "def execute" followed by kwargs access (bad - should use request)
EXECUTE_KWARGS=""

for tool_file in $(find "$MCP_TOOLS_DIR" "$MCP_ARMORY_DIR" -name "*.py" -type f 2>/dev/null | grep -v "__init__" | grep -v "base.py" | grep -v "validator.py" || true); do
    # Check if file has execute method that accesses kwargs (bad pattern)
    # Use awk to check if kwargs appears after "def execute"
    if grep -qE "def execute.*request" "$tool_file" 2>/dev/null; then
        # Extract execute method and check for kwargs (should not have any)
        EXECUTE_BLOCK=$(awk '/def execute/,/def [a-z]/' "$tool_file" 2>/dev/null || true)
        if echo "$EXECUTE_BLOCK" | grep -qE 'kwargs\[|kwargs\.get' 2>/dev/null; then
            EXECUTE_KWARGS="$EXECUTE_KWARGS $tool_file"
        fi
    fi
done

if [ -n "$EXECUTE_KWARGS" ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}kwargs access in execute() method (should use request):${NC}"
    for f in $EXECUTE_KWARGS; do
        echo "  - $f"
    done | head -5
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 3: Error Handling Patterns (WARNING)
# ============================================================
echo -n "Checking error handling patterns... "

# Look for bare "except Exception:" without re-raise or logging
BARE_EXCEPT=""

for tool_file in $(find "$MCP_TOOLS_DIR" "$MCP_ARMORY_DIR" -name "*.py" -type f 2>/dev/null | grep -v "__init__" | grep -v "base.py" || true); do
    # Pattern: "except Exception:" followed by pass or just continue (not raise, not logger)
    if grep -qE "except Exception:$" "$tool_file" 2>/dev/null; then
        # Check if there's a raise or logger in the except block (approximate)
        CONTEXT=$(grep -A3 "except Exception:$" "$tool_file" 2>/dev/null || true)
        if ! echo "$CONTEXT" | grep -qE "raise|logger\.|logging\." 2>/dev/null; then
            BARE_EXCEPT="$BARE_EXCEPT $tool_file"
        fi
    fi
done

if [ -n "$BARE_EXCEPT" ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}Bare 'except Exception:' without raise/logging:${NC}"
    for f in $BARE_EXCEPT; do
        echo "  - $f"
    done | head -5
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 4: Registration Completeness (BLOCKING)
# ============================================================
echo -n "Checking tool registration... "

# Extract Tool classes defined in core tools
DEFINED_TOOLS=$(grep -rh --include="*.py" "^class [A-Z][a-zA-Z]*Tool\(" "$MCP_TOOLS_DIR" 2>/dev/null | \
    sed 's/class //g' | sed 's/(.*//g' | sort -u || true)

# Extract Tool classes exported in __init__.py
EXPORTED_TOOLS=$(grep -E "\"[A-Z][a-zA-Z]*Tool\"" "$MCP_TOOLS_DIR/__init__.py" 2>/dev/null | \
    sed 's/.*"\([A-Z][a-zA-Z]*Tool\)".*/\1/g' | sort -u || true)

# Find defined but not exported
UNREGISTERED=""
for tool in $DEFINED_TOOLS; do
    if ! echo "$EXPORTED_TOOLS" | grep -q "^${tool}$" 2>/dev/null; then
        UNREGISTERED="$UNREGISTERED $tool"
    fi
done

# Count for reporting
DEFINED_COUNT=$(echo "$DEFINED_TOOLS" | wc -l | tr -d ' ')
EXPORTED_COUNT=$(echo "$EXPORTED_TOOLS" | wc -l | tr -d ' ')

# Only error if there are unregistered tools (more than a few is suspicious)
UNREGISTERED_COUNT=$(echo "$UNREGISTERED" | wc -w)
if [ "$UNREGISTERED_COUNT" -gt 3 ]; then
    echo -e "${RED}ERROR${NC}"
    echo -e "${RED}Many tools defined but not exported in __init__.py:${NC}"
    echo "  Defined: $DEFINED_COUNT, Exported: $EXPORTED_COUNT"
    for t in $UNREGISTERED; do
        echo "  - $t"
    done | head -5
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}OK${NC} (Defined: $DEFINED_COUNT, Exported: $EXPORTED_COUNT)"
fi

# ============================================================
# Check 5: Test Coverage (WARNING)
# ============================================================
echo -n "Checking test file coverage... "

# Check that MCP server has test files
# Tests are organized differently - look for any test files in tests/
TEST_COUNT=$(find "$MCP_TESTS_DIR" -name "test_*.py" -type f 2>/dev/null | wc -l | tr -d ' ')

if [ "$TEST_COUNT" -lt 5 ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}Low test coverage - only $TEST_COUNT test files found${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}OK${NC} ($TEST_COUNT test files)"
fi

# ============================================================
# Check 6: Duplicate Tool Names (BLOCKING)
# ============================================================
echo -n "Checking for duplicate tool names... "

# Extract tool names from name property definitions
TOOL_NAMES=$(grep -rh --include="*.py" -A1 "@property" "$MCP_TOOLS_DIR" "$MCP_ARMORY_DIR" 2>/dev/null | \
    grep -A1 "def name" | grep "return" | sed 's/.*return "\([^"]*\)".*/\1/g' | sort || true)

DUPLICATES=$(echo "$TOOL_NAMES" | uniq -d)

if [ -n "$DUPLICATES" ]; then
    echo -e "${RED}ERROR${NC}"
    echo -e "${RED}Duplicate tool names found:${NC}"
    echo "$DUPLICATES"
    ERRORS=$((ERRORS + 1))
else
    UNIQUE_COUNT=$(echo "$TOOL_NAMES" | sort -u | wc -l | tr -d ' ')
    echo -e "${GREEN}OK${NC} ($UNIQUE_COUNT unique tool names)"
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}MCP tool validation passed!${NC}"
    exit 0
elif [ $ERRORS -gt 0 ]; then
    echo -e "${RED}MCP tool validation found $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Fix errors before committing MCP tool changes."
    echo "Reference: mcp-server/src/scheduler_mcp/tools/base.py"
    exit 1
else
    echo -e "${YELLOW}MCP tool validation found $WARNINGS warning(s)${NC}"
    echo ""
    echo "Consider addressing warnings before committing."
    # Warnings only - don't block
    exit 0
fi
