#!/usr/bin/env python3
"""
Development environment setup script.

Automates setup of local development environment:
- Creates Python virtual environment
- Installs backend dependencies
- Installs frontend dependencies
- Creates .env file from template
- Initializes database
- Seeds test data

Usage:
    python scripts/dev/setup_dev_env.py
    python scripts/dev/setup_dev_env.py --skip-seed
    python scripts/dev/setup_dev_env.py --frontend-only
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, cwd: Path = None, check: bool = True) -> bool:
    """Run shell command."""
    try:
        print(f"  Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0 and check:
            print(f"  Error: {result.stderr}")
            return False

        return True

    except subprocess.CalledProcessError as e:
        print(f"  Error: {e.stderr}")
        return False


def setup_backend(project_root: Path) -> bool:
    """Setup backend environment."""
    print("\n" + "=" * 60)
    print("Setting up backend...")
    print("=" * 60)

    backend_dir = project_root / "backend"

    # Create virtual environment
    print("\n1. Creating Python virtual environment...")
    venv_dir = backend_dir / "venv"

    if venv_dir.exists():
        print("  ✓ Virtual environment already exists")
    else:
        if not run_command(["python3", "-m", "venv", "venv"], cwd=backend_dir):
            return False
        print("  ✓ Virtual environment created")

    # Install dependencies
    print("\n2. Installing Python dependencies...")
    pip_cmd = str(venv_dir / "bin" / "pip")

    if not run_command([pip_cmd, "install", "--upgrade", "pip"], cwd=backend_dir):
        return False

    if not run_command([pip_cmd, "install", "-r", "requirements.txt"], cwd=backend_dir):
        return False

    print("  ✓ Dependencies installed")

    # Create .env file
    print("\n3. Creating .env file...")
    env_file = backend_dir.parent / ".env"
    env_example = backend_dir.parent / ".env.example"

    if env_file.exists():
        print("  ✓ .env file already exists")
    elif env_example.exists():
        env_file.write_text(env_example.read_text())
        print("  ✓ .env file created from template")
        print("  ⚠ Remember to update .env with your local settings!")
    else:
        print("  ⚠ Warning: .env.example not found")

    print("\n✓ Backend setup complete")
    return True


def setup_frontend(project_root: Path) -> bool:
    """Setup frontend environment."""
    print("\n" + "=" * 60)
    print("Setting up frontend...")
    print("=" * 60)

    frontend_dir = project_root / "frontend"

    if not frontend_dir.exists():
        print("  ⚠ Frontend directory not found, skipping")
        return True

    # Install dependencies
    print("\n1. Installing Node.js dependencies...")

    if not run_command(["npm", "install"], cwd=frontend_dir):
        return False

    print("  ✓ Dependencies installed")

    print("\n✓ Frontend setup complete")
    return True


def init_database(project_root: Path) -> bool:
    """Initialize database."""
    print("\n" + "=" * 60)
    print("Initializing database...")
    print("=" * 60)

    backend_dir = project_root / "backend"
    python_cmd = str(backend_dir / "venv" / "bin" / "python")

    # Run Alembic migrations
    print("\n1. Running database migrations...")

    if not run_command(["alembic", "upgrade", "head"], cwd=backend_dir):
        print("  ⚠ Migration failed (database may not be running)")
        return False

    print("  ✓ Migrations applied")

    print("\n✓ Database initialized")
    return True


def seed_test_data(project_root: Path) -> bool:
    """Seed test data."""
    print("\n" + "=" * 60)
    print("Seeding test data...")
    print("=" * 60)

    backend_dir = project_root / "backend"
    python_cmd = str(backend_dir / "venv" / "bin" / "python")

    # Generate blocks
    print("\n1. Generating blocks for academic year...")
    if not run_command(
        [python_cmd, "../scripts/generate_blocks.py", "--academic-year", "2025"],
        cwd=backend_dir,
    ):
        return False

    print("  ✓ Blocks generated")

    # Seed people
    print("\n2. Seeding people...")
    if not run_command(
        [python_cmd, "../scripts/seed_people.py"],
        cwd=backend_dir,
    ):
        return False

    print("  ✓ People seeded")

    # Seed templates
    print("\n3. Seeding rotation templates...")
    if not run_command(
        [python_cmd, "../scripts/seed_templates.py"],
        cwd=backend_dir,
    ):
        return False

    print("  ✓ Templates seeded")

    print("\n✓ Test data seeded")
    return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Development environment setup script"
    )
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Only setup backend",
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Only setup frontend",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip database initialization",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip test data seeding",
    )

    args = parser.parse_args()

    try:
        # Determine project root
        project_root = Path(__file__).parent.parent.parent

        print("=" * 60)
        print("Development Environment Setup")
        print("=" * 60)
        print(f"\nProject root: {project_root}")

        success = True

        # Setup backend
        if not args.frontend_only:
            if not setup_backend(project_root):
                success = False

        # Setup frontend
        if not args.backend_only:
            if not setup_frontend(project_root):
                success = False

        # Initialize database
        if not args.backend_only and not args.skip_db:
            if not init_database(project_root):
                success = False

        # Seed test data
        if not args.backend_only and not args.skip_db and not args.skip_seed:
            if not seed_test_data(project_root):
                success = False

        # Print summary
        print("\n" + "=" * 60)
        if success:
            print("✓ Development environment setup complete!")
            print("\nNext steps:")
            print("  1. Review and update .env file with your settings")
            print("  2. Start Docker services: docker-compose up -d")
            print("  3. Start backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
            print("  4. Start frontend: cd frontend && npm run dev")
        else:
            print("✗ Setup completed with errors")
            print("\nPlease resolve the errors and try again.")

        print("=" * 60)

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\nAborted by user")
        return 130

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
