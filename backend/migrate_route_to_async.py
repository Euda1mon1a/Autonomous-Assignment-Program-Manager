#!/usr/bin/env python3
"""
Automated route migration script: Sync to Async
Part of Session 44: Backend Async Migration

This script automatically converts synchronous route handlers to async.
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple


def migrate_imports(content: str) -> str:
    """Migrate imports from sync to async."""
    # Replace Session with AsyncSession
    content = re.sub(
        r'from sqlalchemy\.orm import Session',
        'from sqlalchemy.ext.asyncio import AsyncSession',
        content
    )

    # Add select import if not present
    if 'from sqlalchemy import' in content and 'select' not in content:
        content = re.sub(
            r'(from sqlalchemy import )',
            r'\1select, ',
            content,
            count=1
        )
    elif 'from sqlalchemy import' not in content:
        # Add select import after other sqlalchemy imports
        content = re.sub(
            r'(from sqlalchemy\.ext\.asyncio import AsyncSession\n)',
            r'\1from sqlalchemy import select\n',
            content
        )

    # Replace get_db with get_async_db
    content = re.sub(
        r'from app\.db\.session import get_db',
        'from app.db.session import get_async_db',
        content
    )

    return content


def migrate_route_handler(content: str) -> str:
    """Convert route handler from sync to async."""
    # Pattern: @router.METHOD(...)\ndef function_name(
    # Replace: def -> async def
    content = re.sub(
        r'(@router\.(get|post|put|delete|patch)\([^)]+\)\s*\n\s*)def\s+',
        r'\1async def ',
        content
    )

    return content


def migrate_db_dependency(content: str) -> str:
    """Migrate database dependency from Session to AsyncSession."""
    # Replace: db: Session = Depends(get_db)
    # With: db: AsyncSession = Depends(get_async_db)
    content = re.sub(
        r'db:\s*Session\s*=\s*Depends\(get_db\)',
        'db: AsyncSession = Depends(get_async_db)',
        content
    )

    return content


def migrate_db_query_calls(content: str) -> str:
    """Convert db.query() calls to await db.execute(select())."""
    # This is a basic conversion - may need manual adjustment for complex queries

    # Pattern 1: db.query(Model).filter(...).first()
    pattern1 = r'db\.query\((\w+)\)\.filter\(([^)]+)\)\.first\(\)'
    replacement1 = r'(await db.execute(select(\1).where(\2))).scalar_one_or_none()'
    content = re.sub(pattern1, replacement1, content)

    # Pattern 2: db.query(Model).filter(...).all()
    pattern2 = r'db\.query\((\w+)\)\.filter\(([^)]+)\)\.all\(\)'
    replacement2 = r'(await db.execute(select(\1).where(\2))).scalars().all()'
    content = re.sub(pattern2, replacement2, content)

    # Pattern 3: db.query(Model).all()
    pattern3 = r'db\.query\((\w+)\)\.all\(\)'
    replacement3 = r'(await db.execute(select(\1))).scalars().all()'
    content = re.sub(pattern3, replacement3, content)

    # Pattern 4: db.query(Model).count()
    pattern4 = r'db\.query\((\w+)\)\.count\(\)'
    replacement4 = r'(await db.execute(select(func.count()).select_from(\1))).scalar_one()'
    content = re.sub(pattern4, replacement4, content)

    return content


def add_await_to_service_calls(content: str) -> str:
    """Add await to common service method calls."""
    # List of common service methods that should be awaited
    service_methods = [
        'execute_swap',
        'validate_swap',
        'rollback_swap',
        'can_rollback',
        'create_assignment',
        'update_assignment',
        'delete_assignment',
        'generate_schedule',
        'validate_schedule',
    ]

    for method in service_methods:
        # Add await if not already present
        content = re.sub(
            rf'(?<!await\s)(\w+)\.{method}\(',
            rf'await \1.{method}(',
            content
        )

    return content


def migrate_db_commit_rollback(content: str) -> str:
    """Add await to db.commit() and db.rollback() calls."""
    content = re.sub(r'(?<!await\s)db\.commit\(\)', 'await db.commit()', content)
    content = re.sub(r'(?<!await\s)db\.rollback\(\)', 'await db.rollback()', content)
    content = re.sub(r'(?<!await\s)db\.flush\(\)', 'await db.flush()', content)
    content = re.sub(r'(?<!await\s)db\.refresh\(', 'await db.refresh(', content)

    return content


def migrate_file(file_path: Path) -> Tuple[bool, str]:
    """
    Migrate a single route file from sync to async.

    Returns:
        (success: bool, message: str)
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        original_content = content

        # Apply migrations in order
        content = migrate_imports(content)
        content = migrate_route_handler(content)
        content = migrate_db_dependency(content)
        content = migrate_db_query_calls(content)
        content = add_await_to_service_calls(content)
        content = migrate_db_commit_rollback(content)

        # Check if any changes were made
        if content == original_content:
            return False, "No changes needed"

        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)

        return True, "Successfully migrated"

    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """Main migration script."""
    if len(sys.argv) < 2:
        print("Usage: python migrate_route_to_async.py <route_file1> [route_file2] ...")
        print("\nExample:")
        print("  python migrate_route_to_async.py backend/app/api/routes/people.py")
        print("  python migrate_route_to_async.py backend/app/api/routes/*.py")
        sys.exit(1)

    files_to_migrate = sys.argv[1:]

    print("=" * 80)
    print("ASYNC MIGRATION SCRIPT - SESSION 44")
    print("=" * 80)
    print()

    results = []
    for file_path_str in files_to_migrate:
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"❌ {file_path.name}: File not found")
            continue

        if file_path.name == '__init__.py':
            print(f"⏭️  {file_path.name}: Skipping __init__.py")
            continue

        success, message = migrate_file(file_path)

        if success:
            print(f"✅ {file_path.name}: {message}")
            results.append((file_path.name, True))
        else:
            print(f"⚠️  {file_path.name}: {message}")
            results.append((file_path.name, False))

    print()
    print("=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)

    successful = sum(1 for _, success in results if success)
    total = len(results)

    print(f"Successfully migrated: {successful}/{total} files")
    print()
    print("⚠️  IMPORTANT: Manual review required!")
    print("   - Check for complex db.query() patterns that need manual conversion")
    print("   - Verify all service calls are properly awaited")
    print("   - Test endpoints to ensure functionality is preserved")
    print()


if __name__ == '__main__':
    main()
