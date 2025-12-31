# CLI Reference

Comprehensive command-line interface for the Residency Scheduler application.

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Command Groups](#command-groups)
  - [Schedule Commands](#schedule-commands)
  - [User Commands](#user-commands)
  - [Compliance Commands](#compliance-commands)
  - [Data Commands](#data-commands)
  - [Maintenance Commands](#maintenance-commands)
  - [Schema Commands](#schema-commands)
  - [Debug Commands](#debug-commands)
- [Examples](#examples)

---

## Installation

The CLI is included with the backend application. Ensure you have the backend environment set up:

```bash
cd backend
source venv/bin/activate
```

## Basic Usage

```bash
# Show help
python -m app.cli --help

# Show help for specific command group
python -m app.cli schedule --help

# Run a command
python -m app.cli schedule generate --start 2025-07-01 --end 2025-09-30
```

### Global Options

- `--debug` - Enable debug logging
- `--version` - Show version information
- `--help` - Show help message

---

## Command Groups

### Schedule Commands

Manage schedule generation and operations.

#### `schedule generate`

Generate a new schedule for specified date range.

**Usage:**
```bash
python -m app.cli schedule generate --start YYYY-MM-DD --end YYYY-MM-DD [OPTIONS]
```

**Options:**
- `--start` (required) - Start date (YYYY-MM-DD)
- `--end` (required) - End date (YYYY-MM-DD)
- `--algorithm` - Algorithm choice: greedy, cp_sat, pulp, hybrid (default: greedy)
- `--timeout` - Solver timeout in seconds (default: 300)
- `--dry-run` - Preview without saving to database
- `--output` - Save schedule to JSON file

**Example:**
```bash
python -m app.cli schedule generate \
    --start 2025-07-01 --end 2025-09-30 \
    --algorithm cp_sat --timeout 300 \
    --output schedule.json
```

#### `schedule validate`

Validate schedule for ACGME compliance.

**Usage:**
```bash
python -m app.cli schedule validate [OPTIONS]
```

**Options:**
- `--block` - Block number to validate (1-13)
- `--start` - Start date for validation range
- `--end` - End date for validation range
- `--report` - Generate detailed validation report

**Example:**
```bash
python -m app.cli schedule validate --block 10 --report
```

#### `schedule export`

Export schedule to various formats.

**Usage:**
```bash
python -m app.cli schedule export --format FORMAT --output PATH [OPTIONS]
```

**Options:**
- `--format` (required) - Export format: json, csv, excel, pdf, ical
- `--output` (required) - Output file path
- `--start` - Start date (defaults to today)
- `--end` - End date (defaults to start + 90 days)
- `--person` - Filter by person ID or email

**Example:**
```bash
python -m app.cli schedule export \
    --format pdf --output schedule.pdf \
    --start 2025-07-01 --end 2025-09-30
```

#### `schedule clear`

Clear (delete) assignments in specified date range.

**Warning:** This is a destructive operation.

**Usage:**
```bash
python -m app.cli schedule clear [OPTIONS]
```

**Options:**
- `--start` - Start date (defaults to today)
- `--end` - End date (defaults to start + 90 days)
- `--confirm` - Skip confirmation prompt

**Example:**
```bash
python -m app.cli schedule clear --start 2025-07-01 --end 2025-09-30
```

---

### User Commands

Manage user accounts and permissions.

#### `user create`

Create a new user account.

**Usage:**
```bash
python -m app.cli user create --email EMAIL [OPTIONS]
```

**Options:**
- `--email` (required) - User email address
- `--password` - User password (will prompt if not provided)
- `--role` - User role (default: RESIDENT)
- `--first-name` - First name
- `--last-name` - Last name
- `--active/--inactive` - Active status (default: active)

**Example:**
```bash
python -m app.cli user create \
    --email admin@example.com \
    --role ADMIN \
    --first-name John \
    --last-name Doe
```

#### `user list`

List all users.

**Usage:**
```bash
python -m app.cli user list [OPTIONS]
```

**Options:**
- `--role` - Filter by role
- `--active/--inactive` - Filter by active status
- `--format` - Output format: table, json, csv (default: table)

**Example:**
```bash
python -m app.cli user list --role RESIDENT --active --format json
```

#### `user reset-password`

Reset user password.

**Usage:**
```bash
python -m app.cli user reset-password --email EMAIL
```

**Options:**
- `--email` (required) - User email address
- `--new-password` - New password (will prompt if not provided)

**Example:**
```bash
python -m app.cli user reset-password --email user@example.com
```

#### `user delete`

Delete a user account.

**Warning:** This is a destructive operation.

**Usage:**
```bash
python -m app.cli user delete --email EMAIL [OPTIONS]
```

**Options:**
- `--email` (required) - User email address
- `--confirm` - Skip confirmation prompt

**Example:**
```bash
python -m app.cli user delete --email user@example.com
```

#### `user set-active`

Set user active/inactive status.

**Usage:**
```bash
python -m app.cli user set-active --email EMAIL --active/--inactive
```

**Example:**
```bash
python -m app.cli user set-active --email user@example.com --inactive
```

---

### Compliance Commands

Check and report ACGME compliance.

#### `compliance check`

Check ACGME compliance for work hour limits.

**Usage:**
```bash
python -m app.cli compliance check [OPTIONS]
```

**Options:**
- `--start` - Start date (defaults to 4 weeks ago)
- `--end` - End date (defaults to today)
- `--person` - Check specific person by ID or email
- `--verbose` - Show detailed violation information

**Example:**
```bash
python -m app.cli compliance check \
    --start 2025-07-01 \
    --person user@example.com \
    --verbose
```

#### `compliance report`

Generate comprehensive ACGME compliance report.

**Usage:**
```bash
python -m app.cli compliance report --start YYYY-MM-DD [OPTIONS]
```

**Options:**
- `--start` (required) - Start date
- `--end` - End date (defaults to start + 1 year)
- `--format` - Report format: markdown, pdf, json (default: markdown)
- `--output` - Output file path

**Example:**
```bash
python -m app.cli compliance report \
    --start 2025-07-01 --end 2026-06-30 \
    --format pdf --output annual_report.pdf
```

#### `compliance statistics`

Show compliance statistics and metrics.

**Usage:**
```bash
python -m app.cli compliance statistics [OPTIONS]
```

**Options:**
- `--start` - Start date (defaults to 1 year ago)
- `--end` - End date (defaults to today)

**Example:**
```bash
python -m app.cli compliance statistics --start 2025-01-01
```

---

### Data Commands

Import, export, and seed data.

#### `data export`

Export database data to file.

**Usage:**
```bash
python -m app.cli data export [OPTIONS]
```

**Options:**
- `--format` - Export format: json, csv, sql (default: json)
- `--output` - Output file path (defaults to data_export_YYYY-MM-DD.ext)
- `--tables` - Comma-separated list of tables to export (defaults to all)

**Example:**
```bash
python -m app.cli data export --format json --output backup.json
python -m app.cli data export --tables persons,assignments --format csv
```

#### `data import`

Import data from file into database.

**Usage:**
```bash
python -m app.cli data import --file PATH [OPTIONS]
```

**Options:**
- `--file` (required) - Input file path
- `--format` - Import format (auto-detected from extension if not specified)
- `--dry-run` - Preview import without making changes
- `--replace` - Replace existing records (instead of skipping)

**Example:**
```bash
python -m app.cli data import --file data.json --dry-run
python -m app.cli data import --file schedule.xlsx --replace
```

#### `data seed`

Seed database with test data.

**Usage:**
```bash
python -m app.cli data seed [OPTIONS]
```

**Options:**
- `--type` - Type of data to seed: all, people, blocks, rotations, assignments (default: all)
- `--academic-year` - Academic year (e.g., 2025 for 2025-2026)

**Example:**
```bash
python -m app.cli data seed --type all --academic-year 2025
python -m app.cli data seed --type people
```

---

### Maintenance Commands

Database maintenance and optimization.

#### `maintenance backup`

Create database backup.

**Usage:**
```bash
python -m app.cli maintenance backup [OPTIONS]
```

**Options:**
- `--output` - Backup file path (defaults to backups/backup_YYYY-MM-DD_HH-MM-SS.dump)
- `--compress` - Compress backup file

**Example:**
```bash
python -m app.cli maintenance backup --compress
python -m app.cli maintenance backup --output my_backup.dump
```

#### `maintenance restore`

Restore database from backup.

**Warning:** This will replace all data in the database.

**Usage:**
```bash
python -m app.cli maintenance restore --file PATH [OPTIONS]
```

**Options:**
- `--file` (required) - Backup file to restore
- `--confirm` - Skip confirmation prompt

**Example:**
```bash
python -m app.cli maintenance restore --file backups/backup_2025-01-01.dump
```

#### `maintenance cleanup`

Clean up old data from database.

**Usage:**
```bash
python -m app.cli maintenance cleanup [OPTIONS]
```

**Options:**
- `--days` - Delete data older than N days (default: 90)
- `--confirm` - Skip confirmation prompt

**Example:**
```bash
python -m app.cli maintenance cleanup --days 90
```

#### `maintenance vacuum`

Vacuum and analyze database.

**Usage:**
```bash
python -m app.cli maintenance vacuum
```

#### `maintenance reindex`

Rebuild database indexes.

**Usage:**
```bash
python -m app.cli maintenance reindex
```

#### `maintenance stats`

Show database statistics.

**Usage:**
```bash
python -m app.cli maintenance stats
```

---

### Schema Commands

Database schema migrations (Alembic wrapper).

#### `schema create`

Create a new database schema migration.

**Usage:**
```bash
python -m app.cli schema create -m MESSAGE [OPTIONS]
```

**Options:**
- `-m, --message` (required) - Migration message
- `--autogenerate` - Auto-generate migration from model changes

**Example:**
```bash
python -m app.cli schema create -m "Add new field" --autogenerate
```

#### `schema upgrade`

Upgrade database to a later version.

**Usage:**
```bash
python -m app.cli schema upgrade [OPTIONS]
```

**Options:**
- `--revision` - Target revision (default: head)
- `--sql` - Generate SQL without applying

**Example:**
```bash
python -m app.cli schema upgrade
python -m app.cli schema upgrade --revision +1
```

#### `schema downgrade`

Downgrade database to a previous version.

**Warning:** May cause data loss.

**Usage:**
```bash
python -m app.cli schema downgrade [OPTIONS]
```

**Options:**
- `--revision` - Target revision (default: -1 = one step back)
- `--sql` - Generate SQL without applying

**Example:**
```bash
python -m app.cli schema downgrade
python -m app.cli schema downgrade --revision base
```

#### `schema history`

Show migration history.

**Usage:**
```bash
python -m app.cli schema history [OPTIONS]
```

**Options:**
- `-v, --verbose` - Show detailed migration information

**Example:**
```bash
python -m app.cli schema history --verbose
```

#### `schema current`

Show current migration revision.

**Usage:**
```bash
python -m app.cli schema current
```

#### `schema show`

Show details of a specific migration.

**Usage:**
```bash
python -m app.cli schema show --revision REVISION
```

**Example:**
```bash
python -m app.cli schema show --revision head
```

---

### Debug Commands

Debugging and diagnostics.

#### `debug check-health`

Run comprehensive system health check.

**Usage:**
```bash
python -m app.cli debug check-health
```

#### `debug test-db`

Test database connection and run diagnostic queries.

**Usage:**
```bash
python -m app.cli debug test-db
```

#### `debug test-redis`

Test Redis connection.

**Usage:**
```bash
python -m app.cli debug test-redis
```

#### `debug show-config`

Show current configuration (sanitized).

**Usage:**
```bash
python -m app.cli debug show-config
```

#### `debug sql`

Execute raw SQL query.

**Warning:** Use with caution. No safety checks.

**Usage:**
```bash
python -m app.cli debug sql --query "QUERY" [OPTIONS]
```

**Options:**
- `--query` (required) - SQL query to execute
- `--format` - Output format: table, json, csv (default: table)

**Example:**
```bash
python -m app.cli debug sql --query "SELECT COUNT(*) FROM persons"
```

#### `debug env-check`

Check environment variables and requirements.

**Usage:**
```bash
python -m app.cli debug env-check
```

---

## Examples

### Complete Workflow Example

```bash
# 1. Check system health
python -m app.cli debug check-health

# 2. Create backup
python -m app.cli maintenance backup --compress

# 3. Seed test data
python -m app.cli data seed --type all --academic-year 2025

# 4. Generate schedule
python -m app.cli schedule generate \
    --start 2025-07-01 --end 2025-09-30 \
    --algorithm cp_sat --timeout 300

# 5. Validate compliance
python -m app.cli compliance check --verbose

# 6. Export schedule
python -m app.cli schedule export \
    --format excel --output schedule.xlsx
```

### User Management Example

```bash
# Create admin user
python -m app.cli user create \
    --email admin@hospital.org \
    --role ADMIN \
    --first-name Admin \
    --last-name User

# List all residents
python -m app.cli user list --role RESIDENT --format table

# Reset password
python -m app.cli user reset-password --email user@example.com
```

### Compliance Reporting Example

```bash
# Check current compliance
python -m app.cli compliance check --verbose

# Generate annual report
python -m app.cli compliance report \
    --start 2025-07-01 --end 2026-06-30 \
    --format markdown --output annual_compliance_report.md

# Show statistics
python -m app.cli compliance statistics --start 2025-01-01
```

---

## Error Handling

All commands return appropriate exit codes:

- `0` - Success
- `1` - General error
- `2` - Warning (some commands)
- `130` - Interrupted by user (Ctrl+C)

Use exit codes in scripts:

```bash
if python -m app.cli schedule validate --block 10; then
    echo "Schedule is valid"
    python -m app.cli schedule export --format pdf --output schedule.pdf
else
    echo "Schedule has violations"
    exit 1
fi
```

---

## See Also

- [Scripts Guide](scripts-guide.md) - Standalone operational scripts
- [API Documentation](../api/README.md) - REST API reference
- [Database Guide](../architecture/database.md) - Database schema
