# CLI Tools and Scripts - Quick Reference

This directory contains operational, development, deployment, and scheduling scripts for the Residency Scheduler.

## 📚 Documentation

- **[CLI Reference](../docs/operations/cli-reference.md)** - Complete CLI command documentation
- **[Scripts Guide](../docs/operations/scripts-guide.md)** - Standalone scripts guide

## 🚀 Quick Start

### Main CLI (Python Module)

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

### Standalone Scripts

Scripts are organized by category:

```
scripts/
├── ops/          # Operations (health checks, backups, secrets)
├── dev/          # Development (setup, test data)
├── deploy/       # Deployment (pre-checks, rollback)
└── scheduling/   # Scheduling (generate, validate, export)
```

## 📋 Common Commands

### Schedule Management

```bash
# Generate schedule
python -m app.cli schedule generate --start 2025-07-01 --end 2025-09-30

# Validate compliance
python -m app.cli compliance check --verbose

# Export to PDF
python -m app.cli schedule export --format pdf --output schedule.pdf
```

### User Management

```bash
# Create admin user
python -m app.cli user create --email admin@example.com --role ADMIN

# List all users
python -m app.cli user list --format table

# Reset password
python -m app.cli user reset-password --email user@example.com
```

### Database Operations

```bash
# Create backup
python -m app.cli maintenance backup --compress

# Run migrations
python -m app.cli schema upgrade

# Show database stats
python -m app.cli maintenance stats
```

### Health Checks

```bash
# System health
python -m app.cli debug check-health

# Or use standalone script
python scripts/ops/health_check.py --format json
```

## 🔧 Operational Scripts

### Health Check
```bash
python scripts/ops/health_check.py
python scripts/ops/health_check.py --format json --output health.json
```

### Database Backup
```bash
python scripts/ops/backup_database.py
python scripts/ops/backup_database.py --retention-days 30 --compress
```

### Secret Rotation
```bash
python scripts/ops/rotate_secrets.py --secret-type all --backup
```

## 🛠️ Development Scripts

### Environment Setup
```bash
python scripts/dev/setup_dev_env.py
python scripts/dev/setup_dev_env.py --backend-only
```

### Generate Test Data
```bash
python scripts/dev/generate_test_data.py --preset small
python scripts/dev/generate_test_data.py --residents 24 --faculty 12
```

## 🚢 Deployment Scripts

### Pre-Deployment Verification
```bash
python scripts/deploy/pre_deploy_check.py
python scripts/deploy/pre_deploy_check.py --skip-tests
```

## 📅 Scheduling Scripts

### Generate Schedule
```bash
python scripts/scheduling/generate_schedule.py --block 10
python scripts/scheduling/generate_schedule.py \
    --start 2025-07-01 --end 2025-09-30 \
    --algorithm cp_sat --timeout 300
```

## 📖 Usage Examples

### Daily Operations
```bash
# Morning routine
python scripts/ops/health_check.py
python -m app.cli compliance check
python -m app.cli schedule export --format pdf --output daily.pdf
```

### Weekly Maintenance
```bash
# Sunday backup
python scripts/ops/backup_database.py --retention-days 30
python -m app.cli maintenance cleanup --days 90
python -m app.cli maintenance vacuum
```

### Development Workflow
```bash
# Setup
python scripts/dev/setup_dev_env.py

# Generate test data
python scripts/dev/generate_test_data.py --preset small

# Test schedule generation
python scripts/scheduling/generate_schedule.py --block 10 --dry-run
```

### Pre-Deployment
```bash
# 1. Verification
python scripts/deploy/pre_deploy_check.py --strict

# 2. Backup
python scripts/ops/backup_database.py

# 3. Migrate
python -m app.cli schema upgrade

# 4. Health check
python scripts/ops/health_check.py
```

## 🔐 Security Notes

- **Never commit secrets** to version control
- Use `--dry-run` flags when testing destructive operations
- Always backup before schema changes or data cleanup
- Rotate secrets regularly using `rotate_secrets.py`
- Use `--confirm` flags carefully in production

## ⚠️ Important Warnings

Commands that modify data require confirmation:
- `schedule clear` - Deletes assignments
- `user delete` - Removes user accounts
- `maintenance cleanup` - Removes old data
- `maintenance restore` - Replaces entire database
- `schema downgrade` - May cause data loss

Always use `--dry-run` when available to preview changes.

## 📊 Exit Codes

All scripts use consistent exit codes:

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | Error |
| 2    | Warning (some scripts) |
| 130  | Interrupted (Ctrl+C) |

## 🤝 Contributing

When adding new scripts:

1. Place in appropriate directory (ops/dev/deploy/scheduling)
2. Follow existing naming conventions
3. Include comprehensive help text and examples
4. Add to documentation (cli-reference.md or scripts-guide.md)
5. Use consistent exit codes
6. Add tests in `backend/tests/scripts/`

## 🆘 Getting Help

```bash
# CLI help
python -m app.cli --help
python -m app.cli schedule --help

# Script help
python scripts/ops/health_check.py --help
python scripts/scheduling/generate_schedule.py --help
```

## 📞 Support

- See [CLI Reference](../docs/operations/cli-reference.md) for detailed command documentation
- See [Scripts Guide](../docs/operations/scripts-guide.md) for script usage patterns
- Check [CLAUDE.md](../CLAUDE.md) for project guidelines
- Review existing scripts for examples

---

**Version:** 1.0.0
**Last Updated:** 2025-12-31
**Maintainer:** Development Team
