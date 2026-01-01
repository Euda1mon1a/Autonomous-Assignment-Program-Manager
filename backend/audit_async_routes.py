#!/usr/bin/env python3
"""
Audit script to identify synchronous routes and database calls.
Part of Session 44: Backend Async Migration
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


def analyze_route_file(file_path: Path) -> dict[str, any]:
    """Analyze a single route file for sync/async patterns."""
    with open(file_path) as f:
        content = f.read()

    # Find all route handlers
    route_pattern = (
        r"@router\.(get|post|put|delete|patch)\([^)]+\)\s*\n\s*(async\s+)?def\s+(\w+)"
    )
    routes = re.findall(route_pattern, content)

    # Find db.query() calls (sync SQLAlchemy)
    db_query_calls = re.findall(r"db\.query\(", content)

    # Find await db.execute() calls (async SQLAlchemy)
    db_execute_calls = re.findall(r"await\s+db\.execute\(", content)

    # Find Session imports (sync)
    sync_session_import = "from sqlalchemy.orm import Session" in content

    # Find AsyncSession imports
    async_session_import = "AsyncSession" in content

    # Categorize routes
    sync_routes = []
    async_routes = []

    for method, is_async, func_name in routes:
        if is_async:
            async_routes.append(f"{method.upper()} {func_name}")
        else:
            sync_routes.append(f"{method.upper()} {func_name}")

    return {
        "file": file_path.name,
        "path": str(file_path),
        "sync_routes": sync_routes,
        "async_routes": async_routes,
        "db_query_count": len(db_query_calls),
        "db_execute_count": len(db_execute_calls),
        "has_sync_session": sync_session_import,
        "has_async_session": async_session_import,
        "total_routes": len(routes),
        "needs_migration": len(sync_routes) > 0 or len(db_query_calls) > 0,
    }


def main():
    routes_dir = Path(
        "/home/user/Autonomous-Assignment-Program-Manager/backend/app/api/routes"
    )

    print("=" * 80)
    print("BACKEND ASYNC MIGRATION AUDIT - SESSION 44")
    print("=" * 80)
    print()

    all_files = []
    total_sync_routes = 0
    total_async_routes = 0
    total_db_query = 0
    total_db_execute = 0
    files_needing_migration = []

    for route_file in sorted(routes_dir.glob("*.py")):
        if route_file.name == "__init__.py":
            continue

        result = analyze_route_file(route_file)
        all_files.append(result)

        total_sync_routes += len(result["sync_routes"])
        total_async_routes += len(result["async_routes"])
        total_db_query += result["db_query_count"]
        total_db_execute += result["db_execute_count"]

        if result["needs_migration"]:
            files_needing_migration.append(result)

    # Print summary
    print("📊 SUMMARY:")
    print(f"   Total route files: {len(all_files)}")
    print(f"   Files needing migration: {len(files_needing_migration)}")
    print(f"   Total sync routes: {total_sync_routes}")
    print(f"   Total async routes: {total_async_routes}")
    print(f"   Total db.query() calls: {total_db_query}")
    print(f"   Total await db.execute() calls: {total_db_execute}")
    print()

    # Print priority files (most sync routes or db.query calls)
    print("=" * 80)
    print("🚨 HIGH PRIORITY FILES (Most sync patterns)")
    print("=" * 80)

    priority_files = sorted(
        files_needing_migration,
        key=lambda x: len(x["sync_routes"]) + x["db_query_count"],
        reverse=True,
    )[:20]

    for i, result in enumerate(priority_files, 1):
        print(f"\n{i}. {result['file']}")
        print(f"   Sync routes: {len(result['sync_routes'])}")
        print(f"   db.query() calls: {result['db_query_count']}")
        if result["sync_routes"]:
            print(f"   Routes to migrate: {', '.join(result['sync_routes'][:5])}")
            if len(result["sync_routes"]) > 5:
                print(
                    f"                      ... and {len(result['sync_routes']) - 5} more"
                )

    print()
    print("=" * 80)
    print("📋 CRITICAL FILES (ACGME Compliance Risk)")
    print("=" * 80)

    critical_files = [
        "auth.py",
        "swap.py",
        "schedule.py",
        "assignments.py",
        "compliance.py",
        "resilience.py",
        "people.py",
    ]

    for filename in critical_files:
        matching = [f for f in all_files if f["file"] == filename]
        if matching:
            result = matching[0]
            print(f"\n{result['file']}:")
            print(
                f"   Status: {'⚠️  NEEDS MIGRATION' if result['needs_migration'] else '✅ Already async'}"
            )
            print(f"   Sync routes: {len(result['sync_routes'])}")
            print(f"   Async routes: {len(result['async_routes'])}")
            print(f"   db.query() calls: {result['db_query_count']}")
            print(f"   db.execute() calls: {result['db_execute_count']}")

    print()
    print("=" * 80)
    print("📝 DETAILED FILE LIST")
    print("=" * 80)

    # Write detailed report
    with open(
        "/home/user/Autonomous-Assignment-Program-Manager/backend/ASYNC_MIGRATION_REPORT.txt",
        "w",
    ) as f:
        f.write("BACKEND ASYNC MIGRATION DETAILED REPORT\n")
        f.write("=" * 80 + "\n\n")

        for result in sorted(all_files, key=lambda x: x["file"]):
            if result["needs_migration"]:
                f.write(f"\n{'=' * 80}\n")
                f.write(f"FILE: {result['file']}\n")
                f.write(f"PATH: {result['path']}\n")
                f.write(f"{'=' * 80}\n")
                f.write("Status: NEEDS MIGRATION\n")
                f.write(f"Total routes: {result['total_routes']}\n")
                f.write(f"Sync routes: {len(result['sync_routes'])}\n")
                f.write(f"Async routes: {len(result['async_routes'])}\n")
                f.write(f"db.query() calls: {result['db_query_count']}\n")
                f.write(f"db.execute() calls: {result['db_execute_count']}\n")
                f.write(f"Has sync Session: {result['has_sync_session']}\n")
                f.write(f"Has AsyncSession: {result['has_async_session']}\n")

                if result["sync_routes"]:
                    f.write("\nSync routes to migrate:\n")
                    for route in result["sync_routes"]:
                        f.write(f"  - {route}\n")

                f.write("\n")

    print("\n✅ Detailed report written to: backend/ASYNC_MIGRATION_REPORT.txt")
    print()


if __name__ == "__main__":
    main()
