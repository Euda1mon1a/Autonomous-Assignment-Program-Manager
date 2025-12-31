#!/usr/bin/env python3
"""
Secret rotation utility.

Rotates application secrets safely:
- JWT secret keys
- API tokens
- Webhook secrets
- Encryption keys

Usage:
    python scripts/ops/rotate_secrets.py --secret-type jwt
    python scripts/ops/rotate_secrets.py --secret-type all --dry-run
    python scripts/ops/rotate_secrets.py --backup
"""

import argparse
import secrets
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))


def generate_secret(length: int = 64) -> str:
    """Generate a cryptographically secure random secret."""
    return secrets.token_urlsafe(length)


def backup_env_file(env_path: Path) -> Path:
    """Create backup of .env file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = env_path.parent / f".env.backup.{timestamp}"

    if env_path.exists():
        backup_path.write_text(env_path.read_text())
        print(f"✓ Created backup: {backup_path}")
        return backup_path
    else:
        raise FileNotFoundError(f".env file not found: {env_path}")


def update_env_file(
    env_path: Path,
    updates: Dict[str, str],
    dry_run: bool = False,
) -> None:
    """Update .env file with new secrets."""
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found: {env_path}")

    lines = env_path.read_text().splitlines()
    updated_lines = []
    updated_keys = set()

    for line in lines:
        # Skip comments and empty lines
        if line.strip().startswith("#") or not line.strip():
            updated_lines.append(line)
            continue

        # Parse key=value
        if "=" in line:
            key = line.split("=", 1)[0].strip()

            if key in updates:
                new_line = f"{key}={updates[key]}"
                updated_lines.append(new_line)
                updated_keys.add(key)

                if dry_run:
                    print(f"  Would update: {key}=[REDACTED]")
                else:
                    print(f"  ✓ Updated: {key}")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Add any missing keys
    for key, value in updates.items():
        if key not in updated_keys:
            new_line = f"{key}={value}"
            updated_lines.append(new_line)

            if dry_run:
                print(f"  Would add: {key}=[REDACTED]")
            else:
                print(f"  ✓ Added: {key}")

    # Write updated file
    if not dry_run:
        env_path.write_text("\n".join(updated_lines) + "\n")


def rotate_jwt_secret(dry_run: bool = False) -> Dict[str, str]:
    """Rotate JWT secret key."""
    print("\nRotating JWT secret key...")

    new_secret = generate_secret(64)

    if dry_run:
        print("  Would generate new SECRET_KEY")
    else:
        print("  ✓ Generated new SECRET_KEY")

    return {"SECRET_KEY": new_secret}


def rotate_webhook_secret(dry_run: bool = False) -> Dict[str, str]:
    """Rotate webhook secret."""
    print("\nRotating webhook secret...")

    new_secret = generate_secret(32)

    if dry_run:
        print("  Would generate new WEBHOOK_SECRET")
    else:
        print("  ✓ Generated new WEBHOOK_SECRET")

    return {"WEBHOOK_SECRET": new_secret}


def rotate_redis_password(dry_run: bool = False) -> Dict[str, str]:
    """Rotate Redis password."""
    print("\nRotating Redis password...")

    new_password = generate_secret(32)

    if dry_run:
        print("  Would generate new REDIS_PASSWORD")
    else:
        print("  ✓ Generated new REDIS_PASSWORD")

    return {"REDIS_PASSWORD": new_password}


def rotate_all_secrets(dry_run: bool = False) -> Dict[str, str]:
    """Rotate all application secrets."""
    updates = {}

    updates.update(rotate_jwt_secret(dry_run))
    updates.update(rotate_webhook_secret(dry_run))
    updates.update(rotate_redis_password(dry_run))

    return updates


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Secret rotation utility"
    )
    parser.add_argument(
        "--secret-type",
        choices=["jwt", "webhook", "redis", "all"],
        default="all",
        help="Type of secret to rotate",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Path to .env file (default: .env)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before rotation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )

    args = parser.parse_args()

    try:
        print("=" * 60)
        print("Secret Rotation Utility")
        print("=" * 60)

        if args.dry_run:
            print("\n⚠ DRY RUN MODE - No changes will be made")

        # Backup .env file
        if args.backup and not args.dry_run:
            backup_env_file(args.env_file)

        # Rotate secrets based on type
        if args.secret_type == "jwt":
            updates = rotate_jwt_secret(args.dry_run)
        elif args.secret_type == "webhook":
            updates = rotate_webhook_secret(args.dry_run)
        elif args.secret_type == "redis":
            updates = rotate_redis_password(args.dry_run)
        elif args.secret_type == "all":
            updates = rotate_all_secrets(args.dry_run)
        else:
            raise ValueError(f"Unknown secret type: {args.secret_type}")

        # Update .env file
        if updates:
            print("\nUpdating .env file...")
            update_env_file(args.env_file, updates, dry_run=args.dry_run)

        print("\n" + "=" * 60)

        if args.dry_run:
            print("✓ Dry run complete - no changes made")
        else:
            print("✓ Secret rotation complete")
            print("\n⚠ WARNING: You must restart all services for changes to take effect!")
            print("  - Restart backend API")
            print("  - Restart Celery workers")
            print("  - Update Redis configuration if password changed")

        print("=" * 60)

        return 0

    except KeyboardInterrupt:
        print("\nAborted by user")
        return 130

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
