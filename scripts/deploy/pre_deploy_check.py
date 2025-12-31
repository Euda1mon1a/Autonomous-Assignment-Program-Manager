#!/usr/bin/env python3
"""
Pre-deployment verification script.

Runs comprehensive checks before deployment:
- Configuration validation
- Database connectivity
- Migration status
- Secret validation
- Dependency check
- Test execution
- Security audit

Usage:
    python scripts/deploy/pre_deploy_check.py
    python scripts/deploy/pre_deploy_check.py --skip-tests
    python scripts/deploy/pre_deploy_check.py --strict
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))


def check_config() -> Tuple[bool, str]:
    """Validate configuration."""
    try:
        from app.config.validator import ConfigValidator

        validator = ConfigValidator()
        result = validator.validate_all()

        if result.is_valid:
            return True, "Configuration valid"
        else:
            return False, f"Configuration errors: {', '.join(result.errors)}"

    except Exception as e:
        return False, f"Configuration check failed: {e}"


def check_database() -> Tuple[bool, str]:
    """Check database connectivity."""
    try:
        from app.db.session import SessionLocal
        from sqlalchemy import text

        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()

        return True, "Database connection successful"

    except Exception as e:
        return False, f"Database connection failed: {e}"


def check_migrations() -> Tuple[bool, str]:
    """Check migration status."""
    try:
        result = subprocess.run(
            ["alembic", "current"],
            cwd="backend",
            capture_output=True,
            text=True,
            check=True,
        )

        if "head" in result.stdout:
            return True, "Migrations up to date"
        else:
            return False, "Migrations not up to date - run 'alembic upgrade head'"

    except Exception as e:
        return False, f"Migration check failed: {e}"


def check_secrets() -> Tuple[bool, str]:
    """Validate secrets."""
    try:
        import os

        required_secrets = ["SECRET_KEY", "WEBHOOK_SECRET"]
        missing = []

        for secret in required_secrets:
            value = os.getenv(secret)
            if not value or len(value) < 32:
                missing.append(secret)

        if missing:
            return False, f"Invalid or missing secrets: {', '.join(missing)}"
        else:
            return True, "Secrets validated"

    except Exception as e:
        return False, f"Secret validation failed: {e}"


def check_dependencies() -> Tuple[bool, str]:
    """Check dependencies are installed."""
    try:
        result = subprocess.run(
            ["pip", "check"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return True, "Dependencies OK"
        else:
            return False, f"Dependency issues: {result.stdout}"

    except Exception as e:
        return False, f"Dependency check failed: {e}"


def run_tests() -> Tuple[bool, str]:
    """Run test suite."""
    try:
        result = subprocess.run(
            ["pytest", "--tb=short", "-q"],
            cwd="backend",
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            return True, "All tests passed"
        else:
            return False, f"Tests failed:\n{result.stdout}"

    except subprocess.TimeoutExpired:
        return False, "Tests timed out after 5 minutes"

    except Exception as e:
        return False, f"Test execution failed: {e}"


def check_security() -> Tuple[bool, str]:
    """Run security checks."""
    try:
        # Check for common security issues
        issues = []

        # Check DEBUG mode
        import os
        if os.getenv("DEBUG", "False").lower() == "true":
            issues.append("DEBUG mode is enabled")

        # Check for weak secrets
        secret_key = os.getenv("SECRET_KEY", "")
        if secret_key in ["", "dev", "test", "password"]:
            issues.append("Weak SECRET_KEY detected")

        if issues:
            return False, f"Security issues: {', '.join(issues)}"
        else:
            return True, "Security checks passed"

    except Exception as e:
        return False, f"Security check failed: {e}"


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Pre-deployment verification script"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip test execution (faster but less thorough)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (not just errors)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Pre-Deployment Verification")
    print("=" * 70)

    checks = [
        ("Configuration", check_config),
        ("Database", check_database),
        ("Migrations", check_migrations),
        ("Secrets", check_secrets),
        ("Dependencies", check_dependencies),
        ("Security", check_security),
    ]

    if not args.skip_tests:
        checks.append(("Tests", run_tests))

    results = []
    all_passed = True

    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        print("-" * 70)

        passed, message = check_func()
        results.append((check_name, passed, message))

        symbol = "✓" if passed else "✗"
        print(f"{symbol} {message}")

        if not passed:
            all_passed = False

    # Summary
    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)

    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)

    print(f"\nPassed: {passed_count}/{total_count}")

    if not all_passed:
        print("\nFailed checks:")
        for name, passed, message in results:
            if not passed:
                print(f"  ✗ {name}: {message}")

    print("\n" + "=" * 70)

    if all_passed:
        print("✓ All checks passed - ready for deployment")
        return 0
    else:
        print("✗ Deployment verification failed - fix issues before deploying")
        return 1


if __name__ == "__main__":
    sys.exit(main())
