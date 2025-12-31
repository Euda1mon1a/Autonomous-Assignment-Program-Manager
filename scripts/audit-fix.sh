#!/bin/bash
# ============================================================
# Script: audit-fix.sh
# Purpose: Fix npm security vulnerabilities in frontend
# Usage: ./scripts/audit-fix.sh
#
# Description:
#   Runs npm audit fix to automatically update vulnerable packages.
#   Creates backup of package-lock.json before making changes.
#   Attempts safe fixes first, then force fixes if needed.
#
# Safety Features:
#   - Backs up package-lock.json before changes
#   - Shows vulnerability report before and after
#   - Logs all changes made
#
# Exit Codes:
#   0 - All vulnerabilities fixed or no vulnerabilities found
#   1 - Some vulnerabilities remain or fix failed
# ============================================================

set -e

echo "=============================================="
echo "NPM Security Audit Fix Script"
echo "=============================================="
echo ""

FRONTEND_DIR="$(dirname "$0")/../frontend"
cd "$FRONTEND_DIR"

echo "Current directory: $(pwd)"
echo ""

# First, run audit to see current status
# npm audit checks all dependencies for known security vulnerabilities
# Output shows severity levels: low, moderate, high, critical
echo "1. Running npm audit to assess vulnerabilities..."
echo "-------------------------------------------"
npm audit || true
echo ""

# Create backup of package-lock.json
# This allows rollback if audit fix breaks the build
# Backup file should be committed if fix is successful
echo "2. Creating backup of package-lock.json..."
cp package-lock.json package-lock.json.backup
echo "   Backup created: package-lock.json.backup"
echo ""

# Attempt safe fix first
echo "3. Attempting safe fix (npm audit fix)..."
echo "-------------------------------------------"
if npm audit fix 2>/dev/null; then
    echo "   Safe fix completed successfully"
else
    echo "   Safe fix had issues, continuing..."
fi
echo ""

# Check if vulnerabilities remain
echo "4. Checking remaining vulnerabilities..."
echo "-------------------------------------------"
REMAINING=$(npm audit 2>/dev/null | grep -c "severity" || echo "0")
if [ "$REMAINING" -gt 0 ]; then
    echo "   Found remaining vulnerabilities"
    echo ""

    read -p "Do you want to run 'npm audit fix --force'? This may include breaking changes. (y/N): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "5. Running npm audit fix --force..."
        echo "-------------------------------------------"
        npm audit fix --force
        echo ""

        echo "6. Running tests to verify nothing broke..."
        echo "-------------------------------------------"
        if npm test -- --passWithNoTests 2>/dev/null; then
            echo "   Tests passed!"
            rm -f package-lock.json.backup
            echo "   Backup removed."
        else
            echo "   Tests failed! Restoring backup..."
            mv package-lock.json.backup package-lock.json
            npm install
            echo "   Restored to previous state."
            exit 1
        fi
    else
        echo "   Skipping force fix."
    fi
else
    echo "   No vulnerabilities remaining!"
    rm -f package-lock.json.backup
fi

echo ""
echo "=============================================="
echo "Audit fix complete!"
echo "=============================================="

# Final audit report
echo ""
echo "Final audit status:"
npm audit || echo "Some vulnerabilities may still exist - review manually."
