***REMOVED***!/usr/bin/env python3
"""
Celery Configuration Verification Script

This script verifies that the Celery configuration is correct and all tasks are registered.
Run from the backend directory: python verify_celery.py
"""

import sys
from pathlib import Path

***REMOVED*** Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def verify_celery_config():
    """Verify Celery configuration and task registration."""
    print("=" * 60)
    print("Celery Configuration Verification")
    print("=" * 60)
    print()

    errors = []
    warnings = []

    ***REMOVED*** 1. Import Celery app
    print("1. Importing Celery app...")
    try:
        from app.core.celery_app import celery_app

        print("   ✓ Celery app imported successfully")
    except Exception as e:
        print(f"   ✗ Failed to import Celery app: {e}")
        errors.append(f"Celery app import failed: {e}")
        return False, errors, warnings

    ***REMOVED*** 2. Check configuration
    print("\n2. Checking Celery configuration...")
    config_checks = {
        "broker_url": celery_app.conf.broker_url,
        "result_backend": celery_app.conf.result_backend,
        "task_serializer": celery_app.conf.task_serializer,
        "accept_content": celery_app.conf.accept_content,
        "timezone": celery_app.conf.timezone,
        "enable_utc": celery_app.conf.enable_utc,
    }

    for key, value in config_checks.items():
        print(f"   {key}: {value}")

    ***REMOVED*** 3. Check task modules are included
    print("\n3. Checking task module includes...")
    includes = celery_app.conf.include
    print(f"   Included modules: {includes}")

    expected_includes = [
        "app.resilience.tasks",
        "app.notifications.tasks",
    ]

    for module in expected_includes:
        if module in includes:
            print(f"   ✓ {module} included")
        else:
            print(f"   ✗ {module} NOT included")
            errors.append(f"Module {module} not included in Celery app")

    ***REMOVED*** 4. Check registered tasks
    print("\n4. Checking registered tasks...")
    try:
        ***REMOVED*** Import task modules to register them

        ***REMOVED*** Get registered tasks
        registered = celery_app.tasks.keys()
        registered_list = [t for t in registered if not t.startswith("celery.")]

        print(f"   Found {len(registered_list)} custom tasks:")
        for task_name in sorted(registered_list):
            print(f"      - {task_name}")

        ***REMOVED*** Check specific expected tasks
        expected_tasks = [
            "app.resilience.tasks.periodic_health_check",
            "app.resilience.tasks.run_contingency_analysis",
            "app.resilience.tasks.precompute_fallback_schedules",
            "app.resilience.tasks.generate_utilization_forecast",
            "app.resilience.tasks.send_resilience_alert",
            "app.resilience.tasks.activate_crisis_response",
            "app.notifications.tasks.send_email",
            "app.notifications.tasks.send_webhook",
        ]

        print("\n   Verifying expected tasks:")
        for task in expected_tasks:
            if task in registered:
                print(f"   ✓ {task}")
            else:
                print(f"   ✗ {task} NOT REGISTERED")
                warnings.append(f"Task {task} not registered")

    except Exception as e:
        print(f"   ✗ Error checking tasks: {e}")
        errors.append(f"Task registration check failed: {e}")

    ***REMOVED*** 5. Check beat schedule
    print("\n5. Checking beat schedule...")
    beat_schedule = celery_app.conf.beat_schedule

    if beat_schedule:
        print(f"   Found {len(beat_schedule)} scheduled tasks:")
        for name, config in beat_schedule.items():
            task = config.get("task", "unknown")
            schedule = config.get("schedule", "unknown")
            queue = config.get("options", {}).get("queue", "default")
            print(f"      - {name}")
            print(f"        Task: {task}")
            print(f"        Schedule: {schedule}")
            print(f"        Queue: {queue}")
    else:
        print("   ✗ No beat schedule configured")
        warnings.append("No beat schedule configured")

    ***REMOVED*** 6. Check task queues
    print("\n6. Checking task queues...")
    task_queues = celery_app.conf.task_queues
    if task_queues:
        print(f"   Configured queues: {list(task_queues.keys())}")
    else:
        print("   Using default queue only")
        warnings.append("Only default queue configured")

    ***REMOVED*** 7. Check task routes
    print("\n7. Checking task routes...")
    task_routes = celery_app.conf.task_routes
    if task_routes:
        print("   Task routing configured:")
        for pattern, route in task_routes.items():
            print(f"      {pattern} -> {route}")
    else:
        print("   No task routing configured")
        warnings.append("No task routing configured")

    ***REMOVED*** Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"   - {error}")

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")

    if not errors and not warnings:
        print("\n✅ All checks passed! Celery is properly configured.")
        return True, errors, warnings
    elif not errors:
        print("\n✅ Configuration is valid but has warnings.")
        return True, errors, warnings
    else:
        print("\n❌ Configuration has errors that need to be fixed.")
        return False, errors, warnings


def check_redis_connection():
    """Check if Redis is available."""
    print("\n" + "=" * 60)
    print("Redis Connection Check")
    print("=" * 60)

    try:
        import redis

        from app.core.config import get_settings

        settings = get_settings()
        print(f"\nConnecting to Redis: {settings.REDIS_URL}")

        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        print("✅ Redis connection successful")

        ***REMOVED*** Get Redis info
        info = r.info()
        print("\nRedis Info:")
        print(f"   Version: {info.get('redis_version', 'unknown')}")
        print(f"   Connected clients: {info.get('connected_clients', 'unknown')}")
        print(f"   Used memory: {info.get('used_memory_human', 'unknown')}")

        return True

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\nNote: Redis must be running for Celery to work.")
        print("Start Redis with: redis-server")
        return False


def check_database_connection():
    """Check if database is available."""
    print("\n" + "=" * 60)
    print("Database Connection Check")
    print("=" * 60)

    try:
        from app.db.session import engine

        print("\nConnecting to database...")
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()

        print("✅ Database connection successful")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nNote: Some Celery tasks require database access.")
        return False


if __name__ == "__main__":
    print("\n🔍 Celery Setup Verification\n")

    ***REMOVED*** Verify Celery configuration
    config_ok, errors, warnings = verify_celery_config()

    ***REMOVED*** Check Redis
    redis_ok = check_redis_connection()

    ***REMOVED*** Check Database
    db_ok = check_database_connection()

    ***REMOVED*** Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    print(f"\nCelery Configuration: {'✅ OK' if config_ok else '❌ FAIL'}")
    print(f"Redis Connection: {'✅ OK' if redis_ok else '❌ FAIL'}")
    print(f"Database Connection: {'✅ OK' if db_ok else '❌ FAIL'}")

    if config_ok and redis_ok and db_ok:
        print("\n🎉 All systems ready! Celery can be started.")
        print("\nStart Celery with:")
        print("   cd backend")
        print("   ../scripts/start-celery.sh both")
        sys.exit(0)
    elif config_ok and redis_ok:
        print("\n✅ Celery is configured correctly!")
        print("⚠️  Database connection failed - some tasks may not work.")
        sys.exit(0)
    elif config_ok:
        print("\n✅ Celery is configured correctly!")
        print("⚠️  Redis is not running - start Redis before starting Celery.")
        sys.exit(1)
    else:
        print("\n❌ Celery configuration has errors - please fix before starting.")
        sys.exit(1)
