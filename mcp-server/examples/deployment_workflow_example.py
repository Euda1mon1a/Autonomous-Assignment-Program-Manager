"""
Example: GitOps-style deployment workflow using MCP deployment tools.

This example demonstrates a complete deployment workflow from validation
to production deployment with proper error handling and monitoring.
"""

import asyncio
import os
from datetime import datetime


async def standard_deployment_workflow():
    """
    Standard deployment workflow: staging -> validation -> production.
    """
    print("=" * 60)
    print("Standard Deployment Workflow Example")
    print("=" * 60)
    print()

    git_ref = "main"
    prod_token = os.getenv("PROD_APPROVAL_TOKEN", "test-token")

    # Step 1: Validate staging deployment
    print("Step 1: Validating staging deployment...")
    print("-" * 60)

    validation_result = {
        "valid": True,
        "environment": "staging",
        "git_ref": git_ref,
        "checks": [
            {
                "check_name": "tests_passed",
                "status": "passed",
                "message": "All tests passed",
            },
            {
                "check_name": "security_scan",
                "status": "passed",
                "message": "No critical vulnerabilities",
            },
        ],
        "blockers": [],
        "warnings": [],
    }

    if not validation_result["valid"]:
        print(f"✗ Validation failed: {validation_result['blockers']}")
        return False

    print("✓ Validation passed!")
    for check in validation_result["checks"]:
        print(f"  • {check['check_name']}: {check['status']}")
    print()

    # Step 2: Run security scan
    print("Step 2: Running security scan...")
    print("-" * 60)

    scan_result = {
        "git_ref": git_ref,
        "passed": True,
        "severity_summary": {"critical": 0, "high": 0, "medium": 2, "low": 5},
    }

    if scan_result["severity_summary"]["critical"] > 0:
        print("✗ Critical vulnerabilities detected!")
        return False

    print("✓ Security scan passed!")
    print(f"  • Critical: {scan_result['severity_summary']['critical']}")
    print(f"  • High: {scan_result['severity_summary']['high']}")
    print(f"  • Medium: {scan_result['severity_summary']['medium']}")
    print(f"  • Low: {scan_result['severity_summary']['low']}")
    print()

    # Step 3: Run smoke tests on staging
    print("Step 3: Running smoke tests on staging...")
    print("-" * 60)

    smoke_result = {
        "environment": "staging",
        "test_suite": "full",
        "passed": True,
        "results": [
            {"check_name": "health_check", "status": "passed"},
            {"check_name": "database_connectivity", "status": "passed"},
            {"check_name": "authentication", "status": "passed"},
        ],
    }

    if not smoke_result["passed"]:
        print("✗ Smoke tests failed!")
        for result in smoke_result["results"]:
            if result["status"] != "passed":
                print(f"  • {result['check_name']}: {result['status']}")
        return False

    print("✓ Smoke tests passed!")
    for result in smoke_result["results"]:
        print(f"  • {result['check_name']}: ✓")
    print()

    # Step 4: Promote to production
    print("Step 4: Promoting to production...")
    print("-" * 60)

    deployment_result = {
        "status": "in_progress",
        "deployment_id": f"deploy-{datetime.now().timestamp()}",
        "staging_version": git_ref,
        "production_version": git_ref,
        "initiated_at": datetime.now(),
        "estimated_duration_minutes": 15,
    }

    print("✓ Deployment initiated!")
    print(f"  • Deployment ID: {deployment_result['deployment_id']}")
    print(f"  • Status: {deployment_result['status']}")
    print(f"  • Estimated duration: {deployment_result['estimated_duration_minutes']} minutes")
    print()

    # Step 5: Monitor deployment
    print("Step 5: Monitoring deployment status...")
    print("-" * 60)

    # Simulate monitoring
    for i in range(3):
        await asyncio.sleep(1)
        progress = (i + 1) * 33
        print(f"  • Progress: {progress}%...")

    deployment_status = {
        "deployment": {
            "deployment_id": deployment_result["deployment_id"],
            "status": "success",
            "health_status": "healthy",
        },
        "health_checks": {
            "api": "healthy",
            "database": "healthy",
            "redis": "healthy",
        },
    }

    print()
    print("✓ Deployment completed successfully!")
    print(f"  • Status: {deployment_status['deployment']['status']}")
    print(f"  • Health: {deployment_status['deployment']['health_status']}")
    print(f"  • API: {deployment_status['health_checks']['api']}")
    print(f"  • Database: {deployment_status['health_checks']['database']}")
    print(f"  • Redis: {deployment_status['health_checks']['redis']}")
    print()

    print("=" * 60)
    print("Deployment workflow completed successfully! 🎉")
    print("=" * 60)

    return True


async def emergency_rollback_workflow():
    """
    Emergency rollback workflow: detect issue -> rollback -> verify.
    """
    print()
    print("=" * 60)
    print("Emergency Rollback Workflow Example")
    print("=" * 60)
    print()

    # Step 1: Detect issue
    print("Step 1: Issue detected in production")
    print("-" * 60)
    print("⚠ Critical error rate spike detected!")
    print("  • Error rate: 15% (threshold: 5%)")
    print("  • Affected service: Authentication")
    print()

    # Step 2: List recent deployments
    print("Step 2: Retrieving recent deployments...")
    print("-" * 60)

    deployments = [
        {
            "version": "v1.2.3",
            "status": "success",
            "initiated_at": "2025-01-15T10:30:00Z",
        },
        {
            "version": "v1.2.2",
            "status": "success",
            "initiated_at": "2025-01-14T14:20:00Z",
        },
        {
            "version": "v1.2.1",
            "status": "success",
            "initiated_at": "2025-01-13T09:15:00Z",
        },
    ]

    print("Recent production deployments:")
    for deployment in deployments:
        print(f"  • {deployment['version']}: {deployment['status']} ({deployment['initiated_at']})")
    print()

    # Step 3: Initiate rollback
    print("Step 3: Initiating rollback...")
    print("-" * 60)

    rollback_result = {
        "status": "rolling_back",
        "environment": "production",
        "from_version": "v1.2.3",
        "to_version": "v1.2.2",
        "rollback_id": f"rollback-{datetime.now().timestamp()}",
    }

    print("✓ Rollback initiated!")
    print(f"  • From: {rollback_result['from_version']}")
    print(f"  • To: {rollback_result['to_version']}")
    print(f"  • Rollback ID: {rollback_result['rollback_id']}")
    print()

    # Step 4: Monitor rollback
    print("Step 4: Monitoring rollback...")
    print("-" * 60)

    for i in range(3):
        await asyncio.sleep(1)
        progress = (i + 1) * 33
        print(f"  • Progress: {progress}%...")

    print()
    print("✓ Rollback completed!")
    print()

    # Step 5: Verify system health
    print("Step 5: Verifying system health...")
    print("-" * 60)

    health_checks = {
        "api": "healthy",
        "database": "healthy",
        "redis": "healthy",
        "error_rate": "0.5%",
    }

    print("System health after rollback:")
    for service, status in health_checks.items():
        print(f"  • {service}: {status}")
    print()

    print("=" * 60)
    print("Rollback completed successfully! 🔄")
    print("=" * 60)

    return True


async def dry_run_deployment():
    """
    Dry-run deployment: test deployment workflow without side effects.
    """
    print()
    print("=" * 60)
    print("Dry-Run Deployment Example")
    print("=" * 60)
    print()

    print("🧪 Running deployment in dry-run mode (no actual changes)")
    print("-" * 60)
    print()

    # All steps run with dry_run=True
    steps = [
        "Validate deployment (dry-run)",
        "Run security scan (dry-run)",
        "Run smoke tests (dry-run)",
        "Promote to production (dry-run)",
    ]

    for step in steps:
        print(f"✓ {step}")
        await asyncio.sleep(0.5)

    print()
    print("=" * 60)
    print("Dry-run completed! No changes were made. ✓")
    print("=" * 60)

    return True


async def main():
    """
    Run all example workflows.
    """
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   Deployment Workflow Automation Examples                 ║")
    print("║   GitOps-style deployments via MCP                        ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    # Example 1: Standard deployment
    success = await standard_deployment_workflow()

    if not success:
        print("Deployment workflow failed!")
        return

    # Example 2: Emergency rollback
    await emergency_rollback_workflow()

    # Example 3: Dry-run
    await dry_run_deployment()

    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   All examples completed!                                 ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    print("To use these tools in production:")
    print("  1. Set environment variables (GITHUB_TOKEN, etc.)")
    print("  2. Import deployment_tools in your MCP client")
    print("  3. Call tools via MCP protocol")
    print()
    print("See docs/deployment-tools.md for full documentation.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
