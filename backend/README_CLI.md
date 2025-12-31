***REMOVED*** Residency Scheduler CLI

Command-line interface for managing the Residency Scheduler application.

***REMOVED******REMOVED*** Installation

```bash
cd backend
pip install -e .
```

***REMOVED******REMOVED*** Usage

***REMOVED******REMOVED******REMOVED*** Authentication

```bash
***REMOVED*** Login
scheduler-cli user login --email admin@example.com

***REMOVED*** Check current user
scheduler-cli user whoami

***REMOVED*** Logout
scheduler-cli user logout
```

***REMOVED******REMOVED******REMOVED*** Database Management

```bash
***REMOVED*** Check database health
scheduler-cli db status

***REMOVED*** Run migrations
scheduler-cli db migrate upgrade

***REMOVED*** Create backup
scheduler-cli db backup create --name my-backup

***REMOVED*** Restore from backup
scheduler-cli db restore from-backup my-backup

***REMOVED*** Seed test data
scheduler-cli db seed all --profile dev
```

***REMOVED******REMOVED******REMOVED*** Schedule Operations

```bash
***REMOVED*** Generate schedule for a block
scheduler-cli schedule generate block 10

***REMOVED*** Validate schedule
scheduler-cli schedule validate block 10

***REMOVED*** Export schedule
scheduler-cli schedule export block 10 --output schedule.json

***REMOVED*** Show conflicts
scheduler-cli schedule conflicts detect 10

***REMOVED*** Analyze coverage
scheduler-cli schedule coverage analyze 10

***REMOVED*** Optimize schedule
scheduler-cli schedule optimize block 10 --objective balanced
```

***REMOVED******REMOVED******REMOVED*** User Management

```bash
***REMOVED*** List all users
scheduler-cli user list all

***REMOVED*** Create resident
scheduler-cli user create resident john@example.com John Doe PGY-1

***REMOVED*** Create faculty
scheduler-cli user create faculty jane@example.com Jane Smith

***REMOVED*** Update user role
scheduler-cli user update role user123 FACULTY

***REMOVED*** Deactivate user
scheduler-cli user update deactivate user123
```

***REMOVED******REMOVED******REMOVED*** ACGME Compliance

```bash
***REMOVED*** Check compliance
scheduler-cli compliance check block 10

***REMOVED*** Check 80-hour rule
scheduler-cli compliance check hours-80 10

***REMOVED*** Check 1-in-7 rule
scheduler-cli compliance check one-in-seven 10

***REMOVED*** Generate compliance report
scheduler-cli compliance report generate 10 --output report.pdf

***REMOVED*** List violations
scheduler-cli compliance violations list --block 10

***REMOVED*** Auto-fix violations
scheduler-cli compliance fix auto 10
```

***REMOVED******REMOVED******REMOVED*** Resilience Framework

```bash
***REMOVED*** Show resilience status
scheduler-cli resilience status show

***REMOVED*** Run N-1 analysis
scheduler-cli resilience analyze n1 10

***REMOVED*** Run N-2 analysis
scheduler-cli resilience analyze n2 10

***REMOVED*** Show active alerts
scheduler-cli resilience alerts list --active

***REMOVED*** Show critical alerts
scheduler-cli resilience alerts critical
```

***REMOVED******REMOVED*** Configuration

The CLI uses configuration from `~/.scheduler-cli/config.yaml`:

```yaml
dev:
  api:
    url: http://localhost:8000
    timeout: 30
  database:
    url: postgresql+asyncpg://scheduler:scheduler@localhost:5432/residency_scheduler
  output:
    format: table
    color: true
    verbose: false
```

***REMOVED******REMOVED*** Testing

```bash
***REMOVED*** Run CLI tests
pytest tests/cli/

***REMOVED*** Run with coverage
pytest tests/cli/ --cov=cli --cov-report=html
```

***REMOVED******REMOVED*** Development

```bash
***REMOVED*** Install in development mode
pip install -e ".[dev]"

***REMOVED*** Run linter
ruff check cli/

***REMOVED*** Format code
ruff format cli/
```

***REMOVED******REMOVED*** Military Medical Context

This CLI is designed for military medical residency programs. Security considerations:

- Never commit real resident/faculty names
- Use sanitized identifiers (PGY-01, FAC-PD) in demos
- Avoid logging sensitive scheduling data
- Ensure backups are encrypted and access-controlled

***REMOVED******REMOVED*** Examples

***REMOVED******REMOVED******REMOVED*** Generate Schedule for Block 10

```bash
***REMOVED*** Dry run to preview
scheduler-cli schedule generate block 10 --dry-run

***REMOVED*** Generate and save
scheduler-cli schedule generate block 10

***REMOVED*** Validate after generation
scheduler-cli schedule validate block 10 --detailed
```

***REMOVED******REMOVED******REMOVED*** Check Compliance and Fix Violations

```bash
***REMOVED*** Check compliance
scheduler-cli compliance check block 10

***REMOVED*** List violations
scheduler-cli compliance violations list --block 10

***REMOVED*** Get fix suggestions
scheduler-cli compliance fix suggest violation-123

***REMOVED*** Auto-fix where possible
scheduler-cli compliance fix auto 10 --max 10
```

***REMOVED******REMOVED******REMOVED*** Backup and Restore

```bash
***REMOVED*** Create compressed backup
scheduler-cli db backup create --compress

***REMOVED*** List backups
scheduler-cli db backup list

***REMOVED*** Restore from backup
scheduler-cli db restore from-backup backup_20241231_120000.sql.gz
```

***REMOVED******REMOVED*** Help

For help on any command:

```bash
scheduler-cli --help
scheduler-cli <command> --help
scheduler-cli <command> <subcommand> --help
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Connection Issues

If you get connection errors, check:

1. API is running: `curl http://localhost:8000/health`
2. Database is accessible: `scheduler-cli db health check`
3. Authentication token is valid: `scheduler-cli user whoami`

***REMOVED******REMOVED******REMOVED*** Authentication Expired

```bash
***REMOVED*** Re-login
scheduler-cli user logout
scheduler-cli user login --email your@email.com
```

***REMOVED******REMOVED******REMOVED*** Database Errors

```bash
***REMOVED*** Check database health
scheduler-cli db health check

***REMOVED*** Check active connections
scheduler-cli db health connections

***REMOVED*** Run VACUUM if performance issues
scheduler-cli db vacuum vacuum --analyze
```
