#!/usr/bin/env python3
"""
Constraint Manager CLI

Command-line tool for viewing and managing constraint configurations.

Usage:
    python constraint_manager_cli.py status          # Show status report
    python constraint_manager_cli.py list            # List all constraints
    python constraint_manager_cli.py enabled         # List enabled constraints
    python constraint_manager_cli.py disabled        # List disabled constraints
    python constraint_manager_cli.py enable NAME     # Enable a constraint
    python constraint_manager_cli.py disable NAME    # Disable a constraint
    python constraint_manager_cli.py preset PRESET   # Apply a preset
    python constraint_manager_cli.py test-all        # Test all disabled constraints

Examples:
    python constraint_manager_cli.py status
    python constraint_manager_cli.py enable OvernightCallGeneration
    python constraint_manager_cli.py preset call_scheduling
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import directly from config module to avoid scheduling/__init__.py dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "config",
    backend_dir / "app" / "scheduling" / "constraints" / "config.py"
)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

get_constraint_config = config_module.get_constraint_config
ConstraintCategory = config_module.ConstraintCategory


def cmd_status(args):
    """Show constraint status report."""
    config = get_constraint_config()
    print(config.get_status_report())


def cmd_list(args):
    """List all constraints."""
    config = get_constraint_config()
    print("All Constraints:")
    print("=" * 70)

    for category in ConstraintCategory:
        constraints = [
            c
            for c in config._configs.values()
            if c.category == category
        ]
        if constraints:
            print(f"\n{category.value}:")
            for constraint in sorted(constraints, key=lambda c: c.name):
                status = "✓ ENABLED" if constraint.enabled else "✗ DISABLED"
                print(f"  [{status}] {constraint.name}")
                if constraint.description:
                    print(f"      {constraint.description}")
                if constraint.weight > 0:
                    print(f"      Weight: {constraint.weight}")


def cmd_enabled(args):
    """List enabled constraints."""
    config = get_constraint_config()
    enabled = config.get_all_enabled()

    print(f"Enabled Constraints ({len(enabled)}):")
    print("=" * 70)

    for constraint in sorted(enabled, key=lambda c: c.name):
        print(f"  ✓ {constraint.name} [{constraint.category.value}]")
        if constraint.description:
            print(f"      {constraint.description}")


def cmd_disabled(args):
    """List disabled constraints."""
    config = get_constraint_config()
    disabled = config.get_all_disabled()

    print(f"Disabled Constraints ({len(disabled)}):")
    print("=" * 70)

    for constraint in sorted(disabled, key=lambda c: c.name):
        print(f"  ✗ {constraint.name} [{constraint.category.value}]")
        if constraint.disable_reason:
            print(f"      Reason: {constraint.disable_reason}")
        if constraint.enable_condition:
            print(f"      Enable when: {constraint.enable_condition}")


def cmd_enable(args):
    """Enable a constraint."""
    config = get_constraint_config()
    name = args.constraint_name

    constraint = config.get(name)
    if not constraint:
        print(f"Error: Constraint '{name}' not found")
        print("\nAvailable constraints:")
        for c in sorted(config._configs.keys()):
            print(f"  - {c}")
        return 1

    if constraint.enabled:
        print(f"Constraint '{name}' is already enabled")
        return 0

    config.enable(name)
    print(f"✓ Enabled constraint: {name}")

    # Show dependencies
    if constraint.dependencies:
        print(f"\nNote: {name} depends on:")
        for dep in constraint.dependencies:
            dep_config = config.get(dep)
            if dep_config:
                status = "✓ enabled" if dep_config.enabled else "✗ disabled"
                print(f"  - {dep} [{status}]")
                if not dep_config.enabled:
                    print(f"    WARNING: Dependency '{dep}' is not enabled!")

    return 0


def cmd_disable(args):
    """Disable a constraint."""
    config = get_constraint_config()
    name = args.constraint_name

    constraint = config.get(name)
    if not constraint:
        print(f"Error: Constraint '{name}' not found")
        return 1

    if not constraint.enabled:
        print(f"Constraint '{name}' is already disabled")
        return 0

    config.disable(name)
    print(f"✗ Disabled constraint: {name}")
    return 0


def cmd_preset(args):
    """Apply a constraint preset."""
    config = get_constraint_config()
    preset = args.preset_name

    valid_presets = [
        "minimal",
        "strict",
        "resilience_tier1",
        "resilience_tier2",
        "call_scheduling",
        "sports_medicine",
    ]

    if preset not in valid_presets:
        print(f"Error: Invalid preset '{preset}'")
        print(f"\nValid presets:")
        for p in valid_presets:
            print(f"  - {p}")
        return 1

    print(f"Applying preset: {preset}")
    config.apply_preset(preset)
    print(f"✓ Preset '{preset}' applied successfully")

    # Show what changed
    print("\nEnabled constraints:")
    for constraint in sorted(config.get_all_enabled(), key=lambda c: c.name):
        print(f"  ✓ {constraint.name}")

    return 0


def cmd_test_all(args):
    """Test that all disabled constraints can be enabled."""
    config = get_constraint_config()
    disabled = config.get_all_disabled()

    print(f"Testing {len(disabled)} disabled constraints...")
    print("=" * 70)

    failed = []
    for constraint in sorted(disabled, key=lambda c: c.name):
        print(f"\nTesting: {constraint.name}")

        # Try to enable
        success = config.enable(constraint.name)
        if not success:
            print(f"  ✗ Failed to enable")
            failed.append(constraint.name)
            continue

        # Check dependencies
        missing_deps = []
        for dep in constraint.dependencies:
            dep_config = config.get(dep)
            if not dep_config or not dep_config.enabled:
                missing_deps.append(dep)

        if missing_deps:
            print(f"  ⚠ Missing dependencies: {', '.join(missing_deps)}")
        else:
            print(f"  ✓ Can be enabled")

        # Disable again
        config.disable(constraint.name)

    print("\n" + "=" * 70)
    if failed:
        print(f"\n✗ {len(failed)} constraints failed:")
        for name in failed:
            print(f"  - {name}")
        return 1
    else:
        print(f"\n✓ All {len(disabled)} disabled constraints can be enabled")
        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Constraint Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Status command
    subparsers.add_parser("status", help="Show constraint status report")

    # List command
    subparsers.add_parser("list", help="List all constraints")

    # Enabled command
    subparsers.add_parser("enabled", help="List enabled constraints")

    # Disabled command
    subparsers.add_parser("disabled", help="List disabled constraints")

    # Enable command
    enable_parser = subparsers.add_parser("enable", help="Enable a constraint")
    enable_parser.add_argument("constraint_name", help="Name of constraint to enable")

    # Disable command
    disable_parser = subparsers.add_parser("disable", help="Disable a constraint")
    disable_parser.add_argument("constraint_name", help="Name of constraint to disable")

    # Preset command
    preset_parser = subparsers.add_parser("preset", help="Apply a constraint preset")
    preset_parser.add_argument("preset_name", help="Name of preset to apply")

    # Test-all command
    subparsers.add_parser("test-all", help="Test all disabled constraints")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    commands = {
        "status": cmd_status,
        "list": cmd_list,
        "enabled": cmd_enabled,
        "disabled": cmd_disabled,
        "enable": cmd_enable,
        "disable": cmd_disable,
        "preset": cmd_preset,
        "test-all": cmd_test_all,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        return cmd_func(args)
    else:
        print(f"Error: Unknown command '{args.command}'")
        return 1


if __name__ == "__main__":
    sys.exit(main())
