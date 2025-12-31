***REMOVED*** CLI Tools and Scripts - Quick Reference

This directory contains operational, development, deployment, and scheduling scripts for the Residency Scheduler.

***REMOVED******REMOVED*** 📚 Documentation

- **[CLI Reference](../docs/operations/cli-reference.md)** - Complete CLI command documentation
- **[Scripts Guide](../docs/operations/scripts-guide.md)** - Standalone scripts guide

***REMOVED******REMOVED*** 🚀 Quick Start

***REMOVED******REMOVED******REMOVED*** Main CLI (Python Module)

```bash
cd backend
source venv/bin/activate
python -m app.cli --help
```

**Command Groups:**
- `schedule` - Schedule generation and management
- `user` - User account management
- `compliance` - ACGME compliance checking
- `data` - Data import/export/seeding
- `maintenance` - Database maintenance
- `schema` - Schema migrations (Alembic)
- `debug` - Debugging and diagnostics

***REMOVED******REMOVED******REMOVED*** Standalone Scripts

Scripts are organized by category:

```
scripts/
├── ops/          ***REMOVED*** Operations (health checks, backups, secrets)
├── dev/          ***REMOVED*** Development (setup, test data)
├── deploy/       ***REMOVED*** Deployment (pre-checks, rollback)
└── scheduling/   ***REMOVED*** Scheduling (generate, validate, export)
```

***REMOVED******REMOVED*** 📋 Common Commands

***REMOVED******REMOVED******REMOVED*** Schedule Management

```bash
***REMOVED*** Generate schedule
python -m app.cli schedule generate --start 2025-07-01 --end 2025-09-30

***REMOVED*** Validate compliance
python -m app.cli compliance check --verbose

***REMOVED*** Export to PDF
python -m app.cli schedule export --format pdf --output schedule.pdf
```

***REMOVED******REMOVED******REMOVED*** User Management

```bash
***REMOVED*** Create admin user
python -m app.cli user create --email admin@example.com --role ADMIN

***REMOVED*** List all users
python -m app.cli user list --format table

***REMOVED*** Reset password
python -m app.cli user reset-password --email user@example.com
```

***REMOVED******REMOVED******REMOVED*** Database Operations

```bash
***REMOVED*** Create backup
python -m app.cli maintenance backup --compress

***REMOVED*** Run migrations
python -m app.cli schema upgrade

***REMOVED*** Show database stats
python -m app.cli maintenance stats
```

***REMOVED******REMOVED******REMOVED*** Health Checks

```bash
***REMOVED*** System health
python -m app.cli debug check-health

***REMOVED*** Or use standalone script
python scripts/ops/health_check.py --format json
```

***REMOVED******REMOVED*** 🔧 Operational Scripts

***REMOVED******REMOVED******REMOVED*** Health Check
```bash
python scripts/ops/health_check.py
python scripts/ops/health_check.py --format json --output health.json
```

***REMOVED******REMOVED******REMOVED*** Database Backup
```bash
python scripts/ops/backup_database.py
python scripts/ops/backup_database.py --retention-days 30 --compress
```

***REMOVED******REMOVED******REMOVED*** Secret Rotation
```bash
python scripts/ops/rotate_secrets.py --secret-type all --backup
```

***REMOVED******REMOVED*** 🛠️ Development Scripts

***REMOVED******REMOVED******REMOVED*** Environment Setup
```bash
python scripts/dev/setup_dev_env.py
python scripts/dev/setup_dev_env.py --backend-only
```

***REMOVED******REMOVED******REMOVED*** Generate Test Data
```bash
python scripts/dev/generate_test_data.py --preset small
python scripts/dev/generate_test_data.py --residents 24 --faculty 12
```

***REMOVED******REMOVED*** 🚢 Deployment Scripts

***REMOVED******REMOVED******REMOVED*** Pre-Deployment Verification
```bash
python scripts/deploy/pre_deploy_check.py
python scripts/deploy/pre_deploy_check.py --skip-tests
```

***REMOVED******REMOVED*** 📅 Scheduling Scripts

***REMOVED******REMOVED******REMOVED*** Generate Schedule
```bash
python scripts/scheduling/generate_schedule.py --block 10
python scripts/scheduling/generate_schedule.py \
    --start 2025-07-01 --end 2025-09-30 \
    --algorithm cp_sat --timeout 300
```

***REMOVED******REMOVED*** 📖 Usage Examples

***REMOVED******REMOVED******REMOVED*** Daily Operations
```bash
***REMOVED*** Morning routine
python scripts/ops/health_check.py
python -m app.cli compliance check
python -m app.cli schedule export --format pdf --output daily.pdf
```

***REMOVED******REMOVED******REMOVED*** Weekly Maintenance
```bash
***REMOVED*** Sunday backup
python scripts/ops/backup_database.py --retention-days 30
python -m app.cli maintenance cleanup --days 90
python -m app.cli maintenance vacuum
```

***REMOVED******REMOVED******REMOVED*** Development Workflow
```bash
***REMOVED*** Setup
python scripts/dev/setup_dev_env.py

***REMOVED*** Generate test data
python scripts/dev/generate_test_data.py --preset small

***REMOVED*** Test schedule generation
python scripts/scheduling/generate_schedule.py --block 10 --dry-run
```

***REMOVED******REMOVED******REMOVED*** Pre-Deployment
```bash
***REMOVED*** 1. Verification
python scripts/deploy/pre_deploy_check.py --strict

***REMOVED*** 2. Backup
python scripts/ops/backup_database.py

***REMOVED*** 3. Migrate
python -m app.cli schema upgrade

***REMOVED*** 4. Health check
python scripts/ops/health_check.py
```

***REMOVED******REMOVED*** 🔐 Security Notes

- **Never commit secrets** to version control
- Use `--dry-run` flags when testing destructive operations
- Always backup before schema changes or data cleanup
- Rotate secrets regularly using `rotate_secrets.py`
- Use `--confirm` flags carefully in production

***REMOVED******REMOVED*** ⚠️ Important Warnings

Commands that modify data require confirmation:
- `schedule clear` - Deletes assignments
- `user delete` - Removes user accounts
- `maintenance cleanup` - Removes old data
- `maintenance restore` - Replaces entire database
- `schema downgrade` - May cause data loss

Always use `--dry-run` when available to preview changes.

***REMOVED******REMOVED*** 📊 Exit Codes

All scripts use consistent exit codes:

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | Error |
| 2    | Warning (some scripts) |
| 130  | Interrupted (Ctrl+C) |

***REMOVED******REMOVED*** 🤝 Contributing

When adding new scripts:

1. Place in appropriate directory (ops/dev/deploy/scheduling)
2. Follow existing naming conventions
3. Include comprehensive help text and examples
4. Add to documentation (cli-reference.md or scripts-guide.md)
5. Use consistent exit codes
6. Add tests in `backend/tests/scripts/`

***REMOVED******REMOVED*** 🆘 Getting Help

```bash
***REMOVED*** CLI help
python -m app.cli --help
python -m app.cli schedule --help

***REMOVED*** Script help
python scripts/ops/health_check.py --help
python scripts/scheduling/generate_schedule.py --help
```

***REMOVED******REMOVED*** 📞 Support

- See [CLI Reference](../docs/operations/cli-reference.md) for detailed command documentation
- See [Scripts Guide](../docs/operations/scripts-guide.md) for script usage patterns
- Check [CLAUDE.md](../CLAUDE.md) for project guidelines
- Review existing scripts for examples

---

**Version:** 1.0.0
**Last Updated:** 2025-12-31
**Maintainer:** Development Team
