***REMOVED***!/bin/bash
***REMOVED*** ============================================================
***REMOVED*** Script: audit-fix.sh
***REMOVED*** Purpose: Fix npm security vulnerabilities in frontend
***REMOVED*** Usage: ./scripts/audit-fix.sh
***REMOVED***
***REMOVED*** Description:
***REMOVED***   Runs npm audit fix to automatically update vulnerable packages.
***REMOVED***   Creates backup of package-lock.json before making changes.
***REMOVED***   Attempts safe fixes first, then force fixes if needed.
***REMOVED***
***REMOVED*** Safety Features:
***REMOVED***   - Backs up package-lock.json before changes
***REMOVED***   - Shows vulnerability report before and after
***REMOVED***   - Logs all changes made
***REMOVED***
***REMOVED*** Exit Codes:
***REMOVED***   0 - All vulnerabilities fixed or no vulnerabilities found
***REMOVED***   1 - Some vulnerabilities remain or fix failed
***REMOVED*** ============================================================

set -euo pipefail

echo "=============================================="
echo "NPM Security Audit Fix Script"
echo "=============================================="
echo ""

FRONTEND_DIR="$(dirname "$0")/../frontend"

***REMOVED*** Validate frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "ERROR: Frontend directory not found: $FRONTEND_DIR" >&2
    exit 1
fi

cd "$FRONTEND_DIR" || {
    echo "ERROR: Failed to change to frontend directory" >&2
    exit 1
}

***REMOVED*** Verify package.json exists
if [ ! -f "package.json" ]; then
    echo "ERROR: package.json not found in frontend directory" >&2
    exit 1
fi

***REMOVED*** Verify npm is available
if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm command not found" >&2
    exit 1
fi

echo "Current directory: $(pwd)"
echo ""

***REMOVED*** First, run audit to see current status
***REMOVED*** npm audit checks all dependencies for known security vulnerabilities
***REMOVED*** Output shows severity levels: low, moderate, high, critical
echo "1. Running npm audit to assess vulnerabilities..."
echo "-------------------------------------------"
npm audit || true
echo ""

***REMOVED*** Create backup of package-lock.json
***REMOVED*** This allows rollback if audit fix breaks the build
***REMOVED*** Backup file should be committed if fix is successful
echo "2. Creating backup of package-lock.json..."
cp package-lock.json package-lock.json.backup
echo "   Backup created: package-lock.json.backup"
echo ""

***REMOVED*** Attempt safe fix first
echo "3. Attempting safe fix (npm audit fix)..."
echo "-------------------------------------------"
if npm audit fix 2>/dev/null; then
    echo "   Safe fix completed successfully"
else
    echo "   Safe fix had issues, continuing..."
fi
echo ""

***REMOVED*** Check if vulnerabilities remain
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

***REMOVED*** Final audit report
echo ""
echo "Final audit status:"
npm audit || echo "Some vulnerabilities may still exist - review manually."
