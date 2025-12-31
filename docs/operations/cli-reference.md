***REMOVED*** CLI Reference

Comprehensive command-line interface for the Residency Scheduler application.

***REMOVED******REMOVED*** Table of Contents

- [Installation](***REMOVED***installation)
- [Basic Usage](***REMOVED***basic-usage)
- [Command Groups](***REMOVED***command-groups)
  - [Schedule Commands](***REMOVED***schedule-commands)
  - [User Commands](***REMOVED***user-commands)
  - [Compliance Commands](***REMOVED***compliance-commands)
  - [Data Commands](***REMOVED***data-commands)
  - [Maintenance Commands](***REMOVED***maintenance-commands)
  - [Schema Commands](***REMOVED***schema-commands)
  - [Debug Commands](***REMOVED***debug-commands)
- [Examples](***REMOVED***examples)

---

***REMOVED******REMOVED*** Installation

The CLI is included with the backend application. Ensure you have the backend environment set up:

```bash
cd backend
source venv/bin/activate
```

***REMOVED******REMOVED*** Basic Usage

```bash
***REMOVED*** Show help
python -m app.cli --help

***REMOVED*** Show help for specific command group
python -m app.cli schedule --help

***REMOVED*** Run a command
python -m app.cli schedule generate --start 2025-07-01 --end 2025-09-30
```

***REMOVED******REMOVED******REMOVED*** Global Options

- `--debug` - Enable debug logging
- `--version` - Show version information
- `--help` - Show help message

---

***REMOVED******REMOVED*** Command Groups

***REMOVED******REMOVED******REMOVED*** Schedule Commands

Manage schedule generation and operations.

***REMOVED******REMOVED******REMOVED******REMOVED*** `schedule generate`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `schedule validate`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `schedule export`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `schedule clear`

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

***REMOVED******REMOVED******REMOVED*** User Commands

Manage user accounts and permissions.

***REMOVED******REMOVED******REMOVED******REMOVED*** `user create`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `user list`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `user reset-password`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `user delete`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `user set-active`

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

***REMOVED******REMOVED******REMOVED*** Compliance Commands

Check and report ACGME compliance.

***REMOVED******REMOVED******REMOVED******REMOVED*** `compliance check`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `compliance report`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `compliance statistics`

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

***REMOVED******REMOVED******REMOVED*** Data Commands

Import, export, and seed data.

***REMOVED******REMOVED******REMOVED******REMOVED*** `data export`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `data import`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `data seed`

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

***REMOVED******REMOVED******REMOVED*** Maintenance Commands

Database maintenance and optimization.

***REMOVED******REMOVED******REMOVED******REMOVED*** `maintenance backup`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `maintenance restore`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `maintenance cleanup`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `maintenance vacuum`

Vacuum and analyze database.

**Usage:**
```bash
python -m app.cli maintenance vacuum
```

***REMOVED******REMOVED******REMOVED******REMOVED*** `maintenance reindex`

Rebuild database indexes.

**Usage:**
```bash
python -m app.cli maintenance reindex
```

***REMOVED******REMOVED******REMOVED******REMOVED*** `maintenance stats`

Show database statistics.

**Usage:**
```bash
python -m app.cli maintenance stats
```

---

***REMOVED******REMOVED******REMOVED*** Schema Commands

Database schema migrations (Alembic wrapper).

***REMOVED******REMOVED******REMOVED******REMOVED*** `schema create`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `schema upgrade`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `schema downgrade`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `schema history`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `schema current`

Show current migration revision.

**Usage:**
```bash
python -m app.cli schema current
```

***REMOVED******REMOVED******REMOVED******REMOVED*** `schema show`

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

***REMOVED******REMOVED******REMOVED*** Debug Commands

Debugging and diagnostics.

***REMOVED******REMOVED******REMOVED******REMOVED*** `debug check-health`

Run comprehensive system health check.

**Usage:**
```bash
python -m app.cli debug check-health
```

***REMOVED******REMOVED******REMOVED******REMOVED*** `debug test-db`

Test database connection and run diagnostic queries.

**Usage:**
```bash
python -m app.cli debug test-db
```

***REMOVED******REMOVED******REMOVED******REMOVED*** `debug test-redis`

Test Redis connection.

**Usage:**
```bash
python -m app.cli debug test-redis
```

***REMOVED******REMOVED******REMOVED******REMOVED*** `debug show-config`

Show current configuration (sanitized).

**Usage:**
```bash
python -m app.cli debug show-config
```

***REMOVED******REMOVED******REMOVED******REMOVED*** `debug sql`

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

***REMOVED******REMOVED******REMOVED******REMOVED*** `debug env-check`

Check environment variables and requirements.

**Usage:**
```bash
python -m app.cli debug env-check
```

---

***REMOVED******REMOVED*** Examples

***REMOVED******REMOVED******REMOVED*** Complete Workflow Example

```bash
***REMOVED*** 1. Check system health
python -m app.cli debug check-health

***REMOVED*** 2. Create backup
python -m app.cli maintenance backup --compress

***REMOVED*** 3. Seed test data
python -m app.cli data seed --type all --academic-year 2025

***REMOVED*** 4. Generate schedule
python -m app.cli schedule generate \
    --start 2025-07-01 --end 2025-09-30 \
    --algorithm cp_sat --timeout 300

***REMOVED*** 5. Validate compliance
python -m app.cli compliance check --verbose

***REMOVED*** 6. Export schedule
python -m app.cli schedule export \
    --format excel --output schedule.xlsx
```

***REMOVED******REMOVED******REMOVED*** User Management Example

```bash
***REMOVED*** Create admin user
python -m app.cli user create \
    --email admin@hospital.org \
    --role ADMIN \
    --first-name Admin \
    --last-name User

***REMOVED*** List all residents
python -m app.cli user list --role RESIDENT --format table

***REMOVED*** Reset password
python -m app.cli user reset-password --email user@example.com
```

***REMOVED******REMOVED******REMOVED*** Compliance Reporting Example

```bash
***REMOVED*** Check current compliance
python -m app.cli compliance check --verbose

***REMOVED*** Generate annual report
python -m app.cli compliance report \
    --start 2025-07-01 --end 2026-06-30 \
    --format markdown --output annual_compliance_report.md

***REMOVED*** Show statistics
python -m app.cli compliance statistics --start 2025-01-01
```

---

***REMOVED******REMOVED*** Error Handling

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

***REMOVED******REMOVED*** See Also

- [Scripts Guide](scripts-guide.md) - Standalone operational scripts
- [API Documentation](../api/README.md) - REST API reference
- [Database Guide](../architecture/database.md) - Database schema
