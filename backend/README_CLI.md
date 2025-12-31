# Residency Scheduler CLI

Command-line interface for managing the Residency Scheduler application.

## Installation

```bash
cd backend
pip install -e .
```

## Usage

### Authentication

```bash
# Login
scheduler-cli user login --email admin@example.com

# Check current user
scheduler-cli user whoami

# Logout
scheduler-cli user logout
```

### Database Management

```bash
# Check database health
scheduler-cli db status

# Run migrations
scheduler-cli db migrate upgrade

# Create backup
scheduler-cli db backup create --name my-backup

# Restore from backup
scheduler-cli db restore from-backup my-backup

# Seed test data
scheduler-cli db seed all --profile dev
```

### Schedule Operations

```bash
# Generate schedule for a block
scheduler-cli schedule generate block 10

# Validate schedule
scheduler-cli schedule validate block 10

# Export schedule
scheduler-cli schedule export block 10 --output schedule.json

# Show conflicts
scheduler-cli schedule conflicts detect 10

# Analyze coverage
scheduler-cli schedule coverage analyze 10

# Optimize schedule
scheduler-cli schedule optimize block 10 --objective balanced
```

### User Management

```bash
# List all users
scheduler-cli user list all

# Create resident
scheduler-cli user create resident john@example.com John Doe PGY-1

# Create faculty
scheduler-cli user create faculty jane@example.com Jane Smith

# Update user role
scheduler-cli user update role user123 FACULTY

# Deactivate user
scheduler-cli user update deactivate user123
```

### ACGME Compliance

```bash
# Check compliance
scheduler-cli compliance check block 10

# Check 80-hour rule
scheduler-cli compliance check hours-80 10

# Check 1-in-7 rule
scheduler-cli compliance check one-in-seven 10

# Generate compliance report
scheduler-cli compliance report generate 10 --output report.pdf

# List violations
scheduler-cli compliance violations list --block 10

# Auto-fix violations
scheduler-cli compliance fix auto 10
```

### Resilience Framework

```bash
# Show resilience status
scheduler-cli resilience status show

# Run N-1 analysis
scheduler-cli resilience analyze n1 10

# Run N-2 analysis
scheduler-cli resilience analyze n2 10

# Show active alerts
scheduler-cli resilience alerts list --active

# Show critical alerts
scheduler-cli resilience alerts critical
```

## Configuration

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

## Testing

```bash
# Run CLI tests
pytest tests/cli/

# Run with coverage
pytest tests/cli/ --cov=cli --cov-report=html
```

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run linter
ruff check cli/

# Format code
ruff format cli/
```

## Military Medical Context

This CLI is designed for military medical residency programs. Security considerations:

- Never commit real resident/faculty names
- Use sanitized identifiers (PGY-01, FAC-PD) in demos
- Avoid logging sensitive scheduling data
- Ensure backups are encrypted and access-controlled

## Examples

### Generate Schedule for Block 10

```bash
# Dry run to preview
scheduler-cli schedule generate block 10 --dry-run

# Generate and save
scheduler-cli schedule generate block 10

# Validate after generation
scheduler-cli schedule validate block 10 --detailed
```

### Check Compliance and Fix Violations

```bash
# Check compliance
scheduler-cli compliance check block 10

# List violations
scheduler-cli compliance violations list --block 10

# Get fix suggestions
scheduler-cli compliance fix suggest violation-123

# Auto-fix where possible
scheduler-cli compliance fix auto 10 --max 10
```

### Backup and Restore

```bash
# Create compressed backup
scheduler-cli db backup create --compress

# List backups
scheduler-cli db backup list

# Restore from backup
scheduler-cli db restore from-backup backup_20241231_120000.sql.gz
```

## Help

For help on any command:

```bash
scheduler-cli --help
scheduler-cli <command> --help
scheduler-cli <command> <subcommand> --help
```

## Troubleshooting

### Connection Issues

If you get connection errors, check:

1. API is running: `curl http://localhost:8000/health`
2. Database is accessible: `scheduler-cli db health check`
3. Authentication token is valid: `scheduler-cli user whoami`

### Authentication Expired

```bash
# Re-login
scheduler-cli user logout
scheduler-cli user login --email your@email.com
```

### Database Errors

```bash
# Check database health
scheduler-cli db health check

# Check active connections
scheduler-cli db health connections

# Run VACUUM if performance issues
scheduler-cli db vacuum vacuum --analyze
```
