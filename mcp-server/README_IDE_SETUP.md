***REMOVED*** MCP Server IDE Setup Guide

This guide explains how to set up and use the Residency Scheduler MCP server with VSCode and Zed editors for local AI-assisted development.

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Prerequisites](***REMOVED***prerequisites)
3. [VSCode Setup](***REMOVED***vscode-setup)
4. [Zed Setup](***REMOVED***zed-setup)
5. [Environment Configuration](***REMOVED***environment-configuration)
6. [Usage](***REMOVED***usage)
7. [Troubleshooting](***REMOVED***troubleshooting)
8. [Security Considerations](***REMOVED***security-considerations)

---

***REMOVED******REMOVED*** Overview

The Residency Scheduler MCP (Model Context Protocol) server provides AI assistants with structured access to:

- **Schedule Status**: Current assignments, coverage metrics, and active issues
- **ACGME Compliance**: Real-time validation against work hour regulations
- **Conflict Detection**: Identification of scheduling conflicts with auto-resolution suggestions
- **Contingency Analysis**: Impact assessment for faculty absences and emergencies
- **Swap Matching**: Intelligent matching for schedule swap requests

***REMOVED******REMOVED******REMOVED*** Architecture

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

***REMOVED******REMOVED*** Prerequisites

***REMOVED******REMOVED******REMOVED*** System Requirements

- Python 3.10 or later
- PostgreSQL 15+ (running and accessible)
- Redis (optional, for enhanced features)

***REMOVED******REMOVED******REMOVED*** Python Environment

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
   ***REMOVED*** Set DATABASE_URL environment variable
   export DATABASE_URL="postgresql://scheduler:your_password@localhost:5432/residency_scheduler"

   ***REMOVED*** Run a quick test
   python -m scheduler_mcp.server
   ```

   The server should start without errors and display initialization messages.

---

***REMOVED******REMOVED*** VSCode Setup

***REMOVED******REMOVED******REMOVED*** Step 1: Install MCP Extension

The MCP extension for VSCode is required to connect to MCP servers. Check the VSCode marketplace for the official MCP extension and install it.

***REMOVED******REMOVED******REMOVED*** Step 2: Configure Environment Variables

Create or edit your `.env` file in the project root:

```bash
***REMOVED*** Copy from template
cp .env.example .env

***REMOVED*** Edit with your actual values
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

***REMOVED******REMOVED******REMOVED*** Step 3: Load Configuration

The configuration is already set up in `.vscode/mcp.json`. VSCode will automatically detect this configuration when the MCP extension is installed.

***REMOVED******REMOVED******REMOVED*** Step 4: Start the MCP Server

1. **Open the Command Palette**: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. **Type**: `MCP: Start Server`
3. **Select**: `residency-scheduler`

The server status will appear in the VSCode status bar.

***REMOVED******REMOVED******REMOVED*** Step 5: Verify Connection

1. **Check the MCP panel**: Look for the MCP icon in the activity bar (left sidebar)
2. **View available resources**:
   - `schedule://status` - Current schedule state
   - `schedule://compliance` - ACGME compliance summary
3. **View available tools**:
   - `validate_schedule_tool`
   - `run_contingency_analysis_tool`
   - `detect_conflicts_tool`
   - `analyze_swap_candidates_tool`

***REMOVED******REMOVED******REMOVED*** VSCode Configuration Details

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
- **PHI protection**: Ensures healthcare data security
- **Approval required**: User confirmation for sensitive operations

---

***REMOVED******REMOVED*** Zed Setup

***REMOVED******REMOVED******REMOVED*** Step 1: Install Zed MCP Support

Zed has built-in MCP support. Ensure you're running the latest version of Zed:

```bash
***REMOVED*** Check version
zed --version
```

***REMOVED******REMOVED******REMOVED*** Step 2: Configure Environment Variables

Same as VSCode - ensure your `.env` file is properly configured (see VSCode Step 2).

***REMOVED******REMOVED******REMOVED*** Step 3: Load Configuration

The configuration is already set up in `.zed/mcp.json`. Zed will automatically detect this when you open the project.

***REMOVED******REMOVED******REMOVED*** Step 4: Start the MCP Server

1. **Open Command Palette**: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. **Type**: `mcp start`
3. **Select**: `residency-scheduler`

Alternatively, you can start it from the MCP panel in Zed's sidebar.

***REMOVED******REMOVED******REMOVED*** Step 5: Verify Connection

1. **Open the MCP panel**: Check the Zed sidebar for the MCP icon
2. **View server status**: Should show "Connected" or "Running"
3. **Test a resource**: Try querying `schedule://status`

***REMOVED******REMOVED******REMOVED*** Zed Configuration Details

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
- **PHI protection enabled**: Healthcare data security
- **Audit logging**: All operations are logged
- **Health checks**: Automatic server health monitoring

---

***REMOVED******REMOVED*** Environment Configuration

***REMOVED******REMOVED******REMOVED*** Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |

***REMOVED******REMOVED******REMOVED*** Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | None |
| `API_BASE_URL` | Main application API URL | None |
| `LOG_LEVEL` | Logging level | `INFO` |

***REMOVED******REMOVED******REMOVED*** Setting Environment Variables

***REMOVED******REMOVED******REMOVED******REMOVED*** Option 1: `.env` file (Recommended)

Create a `.env` file in the project root:

```bash
DATABASE_URL=postgresql://scheduler:mypassword@localhost:5432/residency_scheduler
REDIS_URL=redis://localhost:6379/0
API_BASE_URL=http://localhost:8000
LOG_LEVEL=INFO
```

**Security Note**: The `.env` file is in `.gitignore` and will NOT be committed.

***REMOVED******REMOVED******REMOVED******REMOVED*** Option 2: Shell environment

```bash
***REMOVED*** Bash/Zsh
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://..."

***REMOVED*** Fish
set -x DATABASE_URL "postgresql://..."
set -x REDIS_URL "redis://..."

***REMOVED*** Windows (PowerShell)
$env:DATABASE_URL = "postgresql://..."
$env:REDIS_URL = "redis://..."
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Option 3: IDE-specific configuration

Both VSCode and Zed support environment variable substitution from the shell environment.

---

***REMOVED******REMOVED*** Usage

***REMOVED******REMOVED******REMOVED*** Querying Resources

Resources provide read-only access to scheduling data.

***REMOVED******REMOVED******REMOVED******REMOVED*** Schedule Status

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

***REMOVED******REMOVED******REMOVED******REMOVED*** ACGME Compliance Summary

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

***REMOVED******REMOVED******REMOVED*** Using Tools

Tools enable active operations and analyses.

***REMOVED******REMOVED******REMOVED******REMOVED*** Validate Schedule

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

***REMOVED******REMOVED******REMOVED******REMOVED*** Detect Conflicts

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

***REMOVED******REMOVED******REMOVED******REMOVED*** Run Contingency Analysis

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

***REMOVED******REMOVED******REMOVED******REMOVED*** Analyze Swap Candidates

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

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Server Won't Start

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem: "Command not found: python"

**Solution**: Ensure Python 3.10+ is installed and in your PATH.

```bash
***REMOVED*** Check Python installation
python --version
***REMOVED*** or
python3 --version

***REMOVED*** If using python3, update the mcp.json command to "python3"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem: "Module 'scheduler_mcp' not found"

**Solution**: Install the MCP server package.

```bash
cd mcp-server
pip install -e .
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem: "DATABASE_URL environment variable not set"

**Solution**: Configure your `.env` file or set the environment variable.

```bash
***REMOVED*** Check if .env exists
ls -la .env

***REMOVED*** If not, copy from example
cp .env.example .env

***REMOVED*** Edit and add your database credentials
nano .env
```

***REMOVED******REMOVED******REMOVED*** Connection Issues

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem: "Failed to connect to database"

**Causes and Solutions**:

1. **PostgreSQL not running**:
   ```bash
   ***REMOVED*** Start PostgreSQL
   docker-compose up -d db
   ***REMOVED*** or
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
   ***REMOVED*** Create database
   createdb residency_scheduler

   ***REMOVED*** Run migrations
   cd backend
   alembic upgrade head
   ```

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem: "Server timeout"

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

***REMOVED******REMOVED******REMOVED*** Performance Issues

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem: "Slow response times"

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

***REMOVED******REMOVED******REMOVED*** Data Issues

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem: "No data returned"

**Solution**: Verify database has data.

```bash
***REMOVED*** Connect to database
psql "postgresql://scheduler:password@localhost:5432/residency_scheduler"

***REMOVED*** Check for data
SELECT COUNT(*) FROM assignments;
SELECT COUNT(*) FROM persons;
SELECT COUNT(*) FROM blocks;
```

If tables are empty, you may need to:
1. Run database migrations
2. Load sample data
3. Run the schedule generation process

---

***REMOVED******REMOVED*** Security Considerations

***REMOVED******REMOVED******REMOVED*** Healthcare Data (PHI) Protection

This application handles **Protected Health Information (PHI)** under HIPAA. Security is critical.

***REMOVED******REMOVED******REMOVED******REMOVED*** Key Security Features

1. **Read-only mode by default**: Prevents accidental data modification
2. **Approval required**: User must confirm sensitive operations
3. **Audit logging**: All MCP operations are logged
4. **PHI redaction**: Sensitive data is masked in logs and error messages
5. **Local-only access**: MCP server runs locally, data stays on your machine

***REMOVED******REMOVED******REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** 1. Protect Environment Variables

```bash
***REMOVED*** NEVER commit .env file
echo ".env" >> .gitignore

***REMOVED*** Use strong database passwords
***REMOVED*** Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** 2. Secure Database Access

```bash
***REMOVED*** Use separate database users for different purposes
***REMOVED*** MCP server should have read-only access when possible

***REMOVED*** Create read-only user
CREATE USER mcp_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE residency_scheduler TO mcp_readonly;
GRANT USAGE ON SCHEMA public TO mcp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;
```

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** 3. Monitor MCP Server Activity

```bash
***REMOVED*** Enable audit logging
LOG_LEVEL=INFO

***REMOVED*** Review logs regularly
tail -f .vscode/mcp.log
```

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** 4. Limit Tool Permissions

The MCP configuration includes `requireApproval: true`, which means:
- You must confirm each tool invocation
- Sensitive operations are logged
- You can audit what the AI assistant is doing

***REMOVED******REMOVED******REMOVED******REMOVED******REMOVED*** 5. Network Security

```bash
***REMOVED*** MCP server should ONLY listen on localhost
***REMOVED*** NEVER expose to external networks

***REMOVED*** Verify in server.py:
***REMOVED*** --host localhost (default)
***REMOVED*** NOT --host 0.0.0.0
```

***REMOVED******REMOVED******REMOVED*** Data Retention

***REMOVED******REMOVED******REMOVED******REMOVED*** Development Data

- Use anonymized or synthetic data for development
- Never use production data in local development
- Regularly purge old development data

***REMOVED******REMOVED******REMOVED******REMOVED*** Logs

```bash
***REMOVED*** Rotate logs to prevent disk space issues
***REMOVED*** Add to .gitignore
echo ".vscode/mcp.log" >> .gitignore
echo ".zed/mcp.log" >> .gitignore

***REMOVED*** Clean up old logs periodically
find . -name "mcp.log*" -mtime +30 -delete
```

***REMOVED******REMOVED******REMOVED*** Credential Management

***REMOVED******REMOVED******REMOVED******REMOVED*** DO NOT

- ❌ Commit `.env` files
- ❌ Hardcode credentials in configuration
- ❌ Share database passwords in chat or documentation
- ❌ Use production credentials in development

***REMOVED******REMOVED******REMOVED******REMOVED*** DO

- ✅ Use `.env` for local credentials
- ✅ Use environment variables for CI/CD
- ✅ Rotate credentials regularly
- ✅ Use separate credentials for development and production
- ✅ Enable database connection encryption (SSL)

***REMOVED******REMOVED******REMOVED*** Compliance

***REMOVED******REMOVED******REMOVED******REMOVED*** HIPAA Requirements

When using the MCP server with PHI:

1. **Access Control**: Only authorized users should have access
2. **Audit Trails**: All access must be logged and auditable
3. **Encryption**: Use encrypted connections to database (SSL/TLS)
4. **Data Minimization**: Only query data you need
5. **Secure Disposal**: Securely delete logs and data when no longer needed

***REMOVED******REMOVED******REMOVED******REMOVED*** ACGME Data

Schedule data may be subject to ACGME reporting requirements:
- Maintain accurate work hour records
- Preserve audit trails for compliance reviews
- Ensure data integrity for validation purposes

---

***REMOVED******REMOVED*** Advanced Configuration

***REMOVED******REMOVED******REMOVED*** Custom Log Levels

```bash
***REMOVED*** Debug mode for troubleshooting
export LOG_LEVEL=DEBUG

***REMOVED*** Quiet mode for production
export LOG_LEVEL=WARNING
```

***REMOVED******REMOVED******REMOVED*** Multiple MCP Servers

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

***REMOVED******REMOVED******REMOVED*** Health Checks

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

***REMOVED******REMOVED*** Additional Resources

***REMOVED******REMOVED******REMOVED*** Documentation

- **MCP Specification**: https://modelcontextprotocol.io/
- **FastMCP Framework**: https://github.com/jlowin/fastmcp
- **ACGME Requirements**: https://www.acgme.org/what-we-do/accreditation/common-program-requirements/
- **Project Documentation**: `/home/user/Autonomous-Assignment-Program-Manager/docs/`

***REMOVED******REMOVED******REMOVED*** Related Files

- **Main README**: `../README.md`
- **Backend Documentation**: `../backend/README.md`
- **CLAUDE.md**: `../CLAUDE.md` (AI development guidelines)
- **API Documentation**: `../docs/api/`

***REMOVED******REMOVED******REMOVED*** Support

For issues or questions:

1. Check this troubleshooting guide
2. Review the main MCP server README: `README.md`
3. Check the project issue tracker
4. Review server logs for error details

---

***REMOVED******REMOVED*** Changelog

***REMOVED******REMOVED******REMOVED*** Version 0.1.0 (2025-12-18)

- Initial release
- VSCode MCP configuration
- Zed MCP configuration
- Environment variable setup
- Security guidelines
- Troubleshooting guide

---

**Remember**: This is a healthcare application handling PHI. Security, compliance, and data protection are paramount. When in doubt, err on the side of caution and consult with your security team.
