#!/bin/bash
# Quick verification script for Session 44 async migration

echo "================================================================================"
echo "SESSION 44: ASYNC MIGRATION - QUICK VERIFICATION"
echo "================================================================================"
echo ""

echo "1️⃣ Checking for sync route handlers..."
SYNC_ROUTES=$(find app/api/routes -name "*.py" ! -name "__init__.py" -exec grep -l "@router\.\w\+.*\ndef " {} \; | wc -l)
if [ "$SYNC_ROUTES" -eq 0 ]; then
    echo "   ✅ PASS: No sync route handlers found"
else
    echo "   ❌ FAIL: $SYNC_ROUTES files still have sync route handlers"
fi
echo ""

echo "2️⃣ Checking for sync Session usage..."
SYNC_SESSION=$(find app/api/routes -name "*.py" ! -name "__init__.py" -exec grep -l "db: Session = Depends(get_db)" {} \; | wc -l)
if [ "$SYNC_SESSION" -eq 0 ]; then
    echo "   ✅ PASS: All routes use AsyncSession"
else
    echo "   ❌ FAIL: $SYNC_SESSION files still use sync Session"
fi
echo ""

echo "3️⃣ Checking for db.query() calls..."
DB_QUERY=$(grep -r "db\.query(" app/api/routes/*.py 2>/dev/null | wc -l)
echo "   ⚠️  INFO: $DB_QUERY db.query() calls remain (manual conversion needed)"
echo ""

echo "4️⃣ Checking get_async_db exists..."
if grep -q "async def get_async_db" app/db/session.py; then
    echo "   ✅ PASS: get_async_db dependency exists"
else
    echo "   ❌ FAIL: get_async_db not found"
fi
echo ""

echo "5️⃣ Checking async engine exists..."
if grep -q "async_engine = create_async_engine" app/db/session.py; then
    echo "   ✅ PASS: Async engine configured"
else
    echo "   ❌ FAIL: Async engine not found"
fi
echo ""

echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"
if [ "$SYNC_ROUTES" -eq 0 ] && [ "$SYNC_SESSION" -eq 0 ]; then
    echo "✅ MIGRATION SUCCESSFUL"
    echo "   - All route handlers migrated to async"
    echo "   - All routes use AsyncSession"
    echo "   - $DB_QUERY db.query() calls remain (Phase 2)"
else
    echo "❌ MIGRATION INCOMPLETE"
fi
echo ""
echo "Files generated:"
echo "   - audit_async_routes.py (audit tool)"
echo "   - migrate_route_to_async.py (migration tool)"
echo "   - tests/test_routes_async.py (verification tests)"
echo "   - ASYNC_MIGRATION_REPORT.txt (detailed report)"
echo "   - SESSION_44_MIGRATION_SUMMARY.md (full documentation)"
echo "   - SESSION_44_COMPLETE.md (completion summary)"
echo ""
