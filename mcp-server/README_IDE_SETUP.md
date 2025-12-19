# MCP Server IDE Setup Guide

This guide explains how to set up and use the Residency Scheduler MCP server with VSCode and Zed editors for local AI-assisted development.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [VSCode Setup](#vscode-setup)
4. [Zed Setup](#zed-setup)
5. [Environment Configuration](#environment-configuration)
6. [Usage](#usage)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)

---

## Overview

The Residency Scheduler MCP (Model Context Protocol) server provides AI assistants with structured access to:

- **Schedule Status**: Current assignments, coverage metrics, and active issues
- **ACGME Compliance**: Real-time validation against work hour regulations
- **Conflict Detection**: Identification of scheduling conflicts with auto-resolution suggestions
- **Contingency Analysis**: Impact assessment for faculty absences and emergencies
- **Swap Matching**: Intelligent matching for schedule swap requests

### Architecture

```
IDE (VSCode/Zed)
    ↓
MCP Client (built into IDE)
    ↓
MCP Server (scheduler_mcp.server)
    ↓
PostgreSQL Database / FastAPI Backend
```

---

## Prerequisites

### System Requirements

- Python 3.10 or later
- PostgreSQL 15+ (running and accessible)
- Redis (optional, for enhanced features)

### Python Environment

1. **Install the MCP server package:**
   ```bash
   cd mcp-server
   pip install -e .
   ```

2. **Verify installation:**
   ```bash
   python -m scheduler_mcp.server --help
   ```

   You should see the help message with available options.

3. **Test database connection:**
   ```bash
   # Set DATABASE_URL environment variable
   export DATABASE_URL="postgresql://scheduler:your_password@localhost:5432/residency_scheduler"

   # Run a quick test
   python -m scheduler_mcp.server
   ```

   The server should start without errors and display initialization messages.

---

## VSCode Setup

### Step 1: Install MCP Extension

The MCP extension for VSCode is required to connect to MCP servers. Check the VSCode marketplace for the official MCP extension and install it.

### Step 2: Configure Environment Variables

Create or edit your `.env` file in the project root:

```bash
# Copy from template
cp .env.example .env

# Edit with your actual values
nano .env
```

Required variables:
```bash
DATABASE_URL=postgresql://scheduler:your_password@localhost:5432/residency_scheduler
```

Optional variables:
```bash
REDIS_URL=redis://localhost:6379/0
API_BASE_URL=http://localhost:8000
LOG_LEVEL=INFO
```

### Step 3: Load Configuration

The configuration is already set up in `.vscode/mcp.json`. VSCode will automatically detect this configuration when the MCP extension is installed.

### Step 4: Start the MCP Server

1. **Open the Command Palette**: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. **Type**: `MCP: Start Server`
3. **Select**: `residency-scheduler`

The server status will appear in the VSCode status bar.

### Step 5: Verify Connection

1. **Check the MCP panel**: Look for the MCP icon in the activity bar (left sidebar)
2. **View available resources**:
   - `schedule://status` - Current schedule state
   - `schedule://compliance` - ACGME compliance summary
3. **View available tools**:
   - `validate_schedule_tool`
   - `run_contingency_analysis_tool`
   - `detect_conflicts_tool`
   - `analyze_swap_candidates_tool`

### VSCode Configuration Details

The `.vscode/mcp.json` file contains:

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "cwd": "${workspaceFolder}/mcp-server",
      "env": {
        "DATABASE_URL": "${env:DATABASE_URL}",
        ...
      }
    }
  }
}
```

Key features:
- **Auto-start disabled**: Prevents accidental server starts
- **Read-only mode**: Prevents unauthorized data modifications
- **Data protection**: Ensures user data security
- **Approval required**: User confirmation for sensitive operations

---

## Zed Setup

### Step 1: Install Zed MCP Support

Zed has built-in MCP support. Ensure you're running the latest version of Zed:

```bash
# Check version
zed --version
```

### Step 2: Configure Environment Variables

Same as VSCode - ensure your `.env` file is properly configured (see VSCode Step 2).

### Step 3: Load Configuration

The configuration is already set up in `.zed/mcp.json`. Zed will automatically detect this when you open the project.

### Step 4: Start the MCP Server

1. **Open Command Palette**: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. **Type**: `mcp start`
3. **Select**: `residency-scheduler`

Alternatively, you can start it from the MCP panel in Zed's sidebar.

### Step 5: Verify Connection

1. **Open the MCP panel**: Check the Zed sidebar for the MCP icon
2. **View server status**: Should show "Connected" or "Running"
3. **Test a resource**: Try querying `schedule://status`

### Zed Configuration Details

The `.zed/mcp.json` file contains:

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": {
        "path": "python",
        "args": ["-m", "scheduler_mcp.server"],
        "cwd": "mcp-server",
        "env": {
          "DATABASE_URL": "$DATABASE_URL",
          ...
        }
      }
    }
  }
}
```

Key features:
- **STDIO transport**: Standard input/output communication
- **Data protection enabled**: User data security
- **Audit logging**: All operations are logged
- **Health checks**: Automatic server health monitoring

---

## Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | None |
| `API_BASE_URL` | Main application API URL | None |
| `LOG_LEVEL` | Logging level | `INFO` |

### Setting Environment Variables

#### Option 1: `.env` file (Recommended)

Create a `.env` file in the project root:

```bash
DATABASE_URL=postgresql://scheduler:mypassword@localhost:5432/residency_scheduler
REDIS_URL=redis://localhost:6379/0
API_BASE_URL=http://localhost:8000
LOG_LEVEL=INFO
```

**Security Note**: The `.env` file is in `.gitignore` and will NOT be committed.

#### Option 2: Shell environment

```bash
# Bash/Zsh
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://..."

# Fish
set -x DATABASE_URL "postgresql://..."
set -x REDIS_URL "redis://..."

# Windows (PowerShell)
$env:DATABASE_URL = "postgresql://..."
$env:REDIS_URL = "redis://..."
```

#### Option 3: IDE-specific configuration

Both VSCode and Zed support environment variable substitution from the shell environment.

---

## Usage

### Querying Resources

Resources provide read-only access to scheduling data.

#### Schedule Status

```json
// Request
{
  "resource": "schedule://status",
  "params": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  }
}

// Response
{
  "total_assignments": 1200,
  "coverage_percentage": 98.5,
  "active_conflicts": 2,
  "assignments": [...]
}
```

#### ACGME Compliance Summary

```json
// Request
{
  "resource": "schedule://compliance",
  "params": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  }
}

// Response
{
  "overall_compliance": true,
  "violations": [],
  "warnings": [
    {
      "person_id": "res_001",
      "issue": "Approaching 80-hour limit",
      "hours": 78.5
    }
  ]
}
```

### Using Tools

Tools enable active operations and analyses.

#### Validate Schedule

```json
{
  "tool": "validate_schedule_tool",
  "params": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "check_work_hours": true,
    "check_supervision": true,
    "check_rest_periods": true,
    "check_consecutive_duty": true
  }
}
```

#### Detect Conflicts

```json
{
  "tool": "detect_conflicts_tool",
  "params": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "conflict_types": ["double_booking", "work_hour_violation"],
    "include_auto_resolution": true
  }
}
```

#### Run Contingency Analysis

```json
{
  "tool": "run_contingency_analysis_tool",
  "params": {
    "scenario": "faculty_absence",
    "affected_person_ids": ["fac_012"],
    "start_date": "2025-01-15",
    "end_date": "2025-01-22",
    "auto_resolve": false
  }
}
```

#### Analyze Swap Candidates

```json
{
  "tool": "analyze_swap_candidates_tool",
  "params": {
    "requester_person_id": "fac_008",
    "assignment_id": "asgn_1234",
    "preferred_start_date": "2025-01-20",
    "preferred_end_date": "2025-01-27",
    "max_candidates": 10
  }
}
```

---

## Troubleshooting

### Server Won't Start

#### Problem: "Command not found: python"

**Solution**: Ensure Python 3.10+ is installed and in your PATH.

```bash
# Check Python installation
python --version
# or
python3 --version

# If using python3, update the mcp.json command to "python3"
```

#### Problem: "Module 'scheduler_mcp' not found"

**Solution**: Install the MCP server package.

```bash
cd mcp-server
pip install -e .
```

#### Problem: "DATABASE_URL environment variable not set"

**Solution**: Configure your `.env` file or set the environment variable.

```bash
# Check if .env exists
ls -la .env

# If not, copy from example
cp .env.example .env

# Edit and add your database credentials
nano .env
```

### Connection Issues

#### Problem: "Failed to connect to database"

**Causes and Solutions**:

1. **PostgreSQL not running**:
   ```bash
   # Start PostgreSQL
   docker-compose up -d db
   # or
   sudo systemctl start postgresql
   ```

2. **Wrong credentials**:
   - Verify `DATABASE_URL` in `.env`
   - Test connection:
     ```bash
     psql "postgresql://scheduler:password@localhost:5432/residency_scheduler"
     ```

3. **Database doesn't exist**:
   ```bash
   # Create database
   createdb residency_scheduler

   # Run migrations
   cd backend
   alembic upgrade head
   ```

#### Problem: "Server timeout"

**Solution**: Increase timeout in IDE configuration.

For VSCode, edit `.vscode/mcp.json`:
```json
{
  "global": {
    "timeout": 60000  // Increase to 60 seconds
  }
}
```

For Zed, edit `.zed/mcp.json`:
```json
{
  "settings": {
    "timeout": 60000
  }
}
```

### Performance Issues

#### Problem: "Slow response times"

**Causes and Solutions**:

1. **Large dataset**:
   - Limit date ranges in queries
   - Use pagination for large result sets

2. **Database performance**:
   - Check database indexes
   - Run `VACUUM ANALYZE` on PostgreSQL
   - Monitor query performance

3. **Network latency**:
   - Use localhost for development
   - Check database connection pool settings

### Data Issues

#### Problem: "No data returned"

**Solution**: Verify database has data.

```bash
# Connect to database
psql "postgresql://scheduler:password@localhost:5432/residency_scheduler"

# Check for data
SELECT COUNT(*) FROM assignments;
SELECT COUNT(*) FROM persons;
SELECT COUNT(*) FROM blocks;
```

If tables are empty, you may need to:
1. Run database migrations
2. Load sample data
3. Run the schedule generation process

---

## Security Considerations

### Data Protection

Security is important for any application handling user data.

#### Key Security Features

1. **Read-only mode by default**: Prevents accidental data modification
2. **Approval required**: User must confirm sensitive operations
3. **Audit logging**: All MCP operations are logged
4. **Data redaction**: Sensitive data is masked in logs and error messages
5. **Local-only access**: MCP server runs locally, data stays on your machine

#### Best Practices

##### 1. Protect Environment Variables

```bash
# NEVER commit .env file
echo ".env" >> .gitignore

# Use strong database passwords
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

##### 2. Secure Database Access

```bash
# Use separate database users for different purposes
# MCP server should have read-only access when possible

# Create read-only user
CREATE USER mcp_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE residency_scheduler TO mcp_readonly;
GRANT USAGE ON SCHEMA public TO mcp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;
```

##### 3. Monitor MCP Server Activity

```bash
# Enable audit logging
LOG_LEVEL=INFO

# Review logs regularly
tail -f .vscode/mcp.log
```

##### 4. Limit Tool Permissions

The MCP configuration includes `requireApproval: true`, which means:
- You must confirm each tool invocation
- Sensitive operations are logged
- You can audit what the AI assistant is doing

##### 5. Network Security

```bash
# MCP server should ONLY listen on localhost
# NEVER expose to external networks

# Verify in server.py:
# --host localhost (default)
# NOT --host 0.0.0.0
```

### Data Retention

#### Development Data

- Use anonymized or synthetic data for development
- Never use production data in local development
- Regularly purge old development data

#### Logs

```bash
# Rotate logs to prevent disk space issues
# Add to .gitignore
echo ".vscode/mcp.log" >> .gitignore
echo ".zed/mcp.log" >> .gitignore

# Clean up old logs periodically
find . -name "mcp.log*" -mtime +30 -delete
```

### Credential Management

#### DO NOT

- ❌ Commit `.env` files
- ❌ Hardcode credentials in configuration
- ❌ Share database passwords in chat or documentation
- ❌ Use production credentials in development

#### DO

- ✅ Use `.env` for local credentials
- ✅ Use environment variables for CI/CD
- ✅ Rotate credentials regularly
- ✅ Use separate credentials for development and production
- ✅ Enable database connection encryption (SSL)

### Compliance

#### Security Best Practices

When using the MCP server with sensitive data:

1. **Access Control**: Only authorized users should have access
2. **Audit Trails**: All access must be logged and auditable
3. **Encryption**: Use encrypted connections to database (SSL/TLS)
4. **Data Minimization**: Only query data you need
5. **Secure Disposal**: Securely delete logs and data when no longer needed

#### ACGME Data

Schedule data may be subject to ACGME reporting requirements:
- Maintain accurate work hour records
- Preserve audit trails for compliance reviews
- Ensure data integrity for validation purposes

---

## Advanced Configuration

### Custom Log Levels

```bash
# Debug mode for troubleshooting
export LOG_LEVEL=DEBUG

# Quiet mode for production
export LOG_LEVEL=WARNING
```

### Multiple MCP Servers

You can run multiple MCP servers for different purposes:

```json
{
  "mcpServers": {
    "scheduler-readonly": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "env": {
        "DATABASE_URL": "postgresql://readonly_user:pass@localhost/scheduler"
      }
    },
    "scheduler-admin": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "env": {
        "DATABASE_URL": "postgresql://admin_user:pass@localhost/scheduler"
      }
    }
  }
}
```

### Health Checks

Both VSCode and Zed configurations include automatic health checks:

```json
{
  "healthCheck": {
    "enabled": true,
    "interval": 60000,  // Check every 60 seconds
    "timeout": 5000     // 5 second timeout
  }
}
```

If the server becomes unresponsive, it will automatically restart.

---

## Additional Resources

### Documentation

- **MCP Specification**: https://modelcontextprotocol.io/
- **FastMCP Framework**: https://github.com/jlowin/fastmcp
- **ACGME Requirements**: https://www.acgme.org/what-we-do/accreditation/common-program-requirements/
- **Project Documentation**: `/home/user/Autonomous-Assignment-Program-Manager/docs/`

### Related Files

- **Main README**: `../README.md`
- **Backend Documentation**: `../backend/README.md`
- **CLAUDE.md**: `../CLAUDE.md` (AI development guidelines)
- **API Documentation**: `../docs/api/`

### Support

For issues or questions:

1. Check this troubleshooting guide
2. Review the main MCP server README: `README.md`
3. Check the project issue tracker
4. Review server logs for error details

---

## Changelog

### Version 0.1.0 (2025-12-18)

- Initial release
- VSCode MCP configuration
- Zed MCP configuration
- Environment variable setup
- Security guidelines
- Troubleshooting guide

---

**Remember**: This is a scheduling application. Security and data protection are important. When in doubt, err on the side of caution.
