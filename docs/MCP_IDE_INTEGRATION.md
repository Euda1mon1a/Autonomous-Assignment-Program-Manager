# MCP IDE Integration Guide

> **Created:** 2025-12-18
> **Purpose:** Local AI-assisted development with VSCode and Zed editors
> **Status:** Ready for use

---

## Overview

This document provides an overview of the Model Context Protocol (MCP) server integration for the Residency Scheduler application. The MCP server enables AI assistants to interact with scheduling data and tools through your IDE.

> **Which Claude tool should I use?** This guide covers IDE-integrated Claude (VSCode, Zed, Antigravity).
> For help choosing between Claude for macOS (chat app), Claude Code (CLI), or IDE integration,
> see [Choosing Your Claude Interface](./guides/AI_AGENT_USER_GUIDE.md#choosing-your-claude-interface).

## What Was Created

### VSCode Configuration Files

Located in `/home/user/Autonomous-Assignment-Program-Manager/.vscode/`:

| File | Purpose | Format |
|------|---------|--------|
| `mcp.json` | MCP server connection configuration | JSON |
| `settings.json` | IDE settings for Python, TypeScript, and MCP | JSONC |
| `extensions.json` | Recommended VSCode extensions | JSONC |
| `MCP_QUICK_START.md` | Quick reference guide | Markdown |

### Zed Configuration Files

Located in `/home/user/Autonomous-Assignment-Program-Manager/.zed/`:

| File | Purpose | Format |
|------|---------|--------|
| `mcp.json` | MCP server connection configuration | JSON |
| `settings.json` | IDE settings for development | JSONC |
| `MCP_QUICK_START.md` | Quick reference guide | Markdown |

### Documentation

Located in `/home/user/Autonomous-Assignment-Program-Manager/mcp-server/`:

| File | Purpose |
|------|---------|
| `README_IDE_SETUP.md` | Complete setup and troubleshooting guide |

### Updated Files

| File | Changes |
|------|---------|
| `.gitignore` | Configured to track IDE configs but exclude logs |

---

## Quick Start

### Prerequisites

1. **Install MCP Server Package**
   ```bash
   cd /home/user/Autonomous-Assignment-Program-Manager/mcp-server
   pip install -e .
   ```

2. **Configure Environment Variables**
   ```bash
   # Copy template
   cp .env.example .env

   # Edit with your credentials
   nano .env
   ```

   Required: `DATABASE_URL`

3. **Verify Database is Running**
   ```bash
   # Using Docker
   docker-compose up -d db

   # Or check PostgreSQL service
   sudo systemctl status postgresql
   ```

### Using in VSCode

1. **Install recommended extensions** (prompted automatically)
2. **Open Command Palette**: `Cmd+Shift+P` or `Ctrl+Shift+P`
3. **Run**: `MCP: Start Server`
4. **Select**: `residency-scheduler`

### Using in Zed

1. **Ensure Zed is up-to-date**
2. **Open Command Palette**: `Cmd+Shift+P` or `Ctrl+Shift+P`
3. **Run**: `mcp start`
4. **Select**: `residency-scheduler`

---

## MCP Server Capabilities

### Resources (Read-Only Data Access)

Resources provide AI assistants with access to scheduling data:

#### `schedule://status`
- **Purpose**: Current schedule state and metrics
- **Data**: Assignments, coverage percentages, active conflicts
- **Parameters**:
  - `start_date` (optional): YYYY-MM-DD format
  - `end_date` (optional): YYYY-MM-DD format

**Example Query:**
```
Show me the schedule status for January 2025
```

#### `schedule://compliance`
- **Purpose**: ACGME compliance analysis
- **Data**: Work hour violations, supervision gaps, warnings
- **Parameters**:
  - `start_date` (optional): YYYY-MM-DD format
  - `end_date` (optional): YYYY-MM-DD format

**Example Query:**
```
Check ACGME compliance for the past 30 days
```

### Tools (Active Operations)

Tools enable AI assistants to perform analyses and validations:

#### `validate_schedule_tool`
- **Purpose**: Validate schedule against ACGME work hour rules
- **Checks**:
  - 80-hour weekly limit
  - Supervision requirements
  - Rest period requirements
  - Consecutive duty limits
- **Returns**: Validation result with detailed violations

**Example Request:**
```
Validate the schedule for February 2025 against all ACGME rules
```

#### `run_contingency_analysis_tool`
- **Purpose**: Analyze impact of absences or emergencies
- **Scenarios**:
  - Faculty absence
  - Resident absence
  - Emergency coverage needs
  - Mass absence events
- **Returns**: Impact assessment and resolution strategies

**Example Request:**
```
Run contingency analysis for Dr. Smith being absent Jan 15-22
```

#### `detect_conflicts_tool`
- **Purpose**: Find scheduling conflicts
- **Detects**:
  - Double bookings
  - Work hour violations
  - Supervision gaps
  - Rest period violations
- **Returns**: Conflicts with auto-resolution suggestions

**Example Request:**
```
Detect all scheduling conflicts in the next two weeks
```

#### `analyze_swap_candidates_tool`
- **Purpose**: Find optimal swap match candidates
- **Analysis**:
  - Rotation compatibility
  - Schedule flexibility
  - Mutual benefit scoring
  - ACGME compliance impact
- **Returns**: Ranked list of swap candidates

**Example Request:**
```
Find swap candidates for Dr. Johnson's clinic shift on Jan 20
```

---

## Configuration Details

### Environment Variables

Both IDE configurations use environment variable substitution:

| Variable | Required | Purpose | Example |
|----------|----------|---------|---------|
| `DATABASE_URL` | Yes | PostgreSQL connection | `postgresql://user:pass@localhost/db` |
| `REDIS_URL` | No | Redis connection | `redis://localhost:6379/0` |
| `API_BASE_URL` | No | Main API endpoint | `http://localhost:8000` |
| `LOG_LEVEL` | No | Logging verbosity | `INFO`, `DEBUG`, `WARNING` |

### VSCode Configuration (`.vscode/mcp.json`)

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

**Key Features:**
- Workspace-relative paths using `${workspaceFolder}`
- Environment variable substitution with `${env:VAR_NAME}`
- Built-in security features (read-only, approval required)
- Automatic health checks every 60 seconds

### Zed Configuration (`.zed/mcp.json`)

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

**Key Features:**
- Project-relative paths
- Shell environment variable substitution
- Data protection enabled
- Audit logging active

---

## Security Features

### Built-in Protection

Both configurations include:

1. **Read-Only Mode**: Prevents accidental data modification
2. **Approval Required**: User confirmation for sensitive operations
3. **Data Protection**: Security measures for user data
4. **Audit Logging**: All operations logged for compliance
5. **Local-Only Access**: Data stays on your machine

### Security Best Practices

1. **Never commit `.env` files**
   - Already in `.gitignore`
   - Contains sensitive credentials

2. **Use read-only database users**
   ```sql
   CREATE USER mcp_readonly WITH PASSWORD 'secure_password';
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;
   ```

3. **Review MCP logs regularly**
   ```bash
   tail -f .vscode/mcp.log  # VSCode
   tail -f .zed/mcp.log     # Zed
   ```

4. **Enable audit logging**
   ```bash
   # In .env
   LOG_LEVEL=INFO  # or DEBUG for detailed logs
   ```

5. **Protect sensitive data**
   - Use anonymized data for development
   - Never use production data locally
   - Securely delete old logs

---

## Troubleshooting

### Common Issues

#### Server Won't Start

**Symptom**: Error when starting MCP server

**Solutions**:
1. Check Python version: `python --version` (need 3.10+)
2. Install MCP server: `cd mcp-server && pip install -e .`
3. Verify DATABASE_URL: `echo $DATABASE_URL`
4. Test database: `psql "$DATABASE_URL"`

#### No Data Returned

**Symptom**: Queries return empty results

**Solutions**:
1. Run migrations: `cd backend && alembic upgrade head`
2. Check database: `psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM persons;"`
3. Verify date ranges in queries

#### Connection Timeouts

**Symptom**: Server takes too long to respond

**Solutions**:
1. Increase timeout in configuration (default: 30s)
2. Check database performance
3. Limit query date ranges
4. Verify network connectivity

#### Environment Variables Not Loading

**Symptom**: "DATABASE_URL not set" error

**Solutions**:
1. Check `.env` file exists: `ls -la .env`
2. Verify format: `cat .env | grep DATABASE_URL`
3. Restart IDE to reload environment
4. Set manually: `export DATABASE_URL="..."`

### Getting Help

1. **Quick Start Guides**:
   - `.vscode/MCP_QUICK_START.md`
   - `.zed/MCP_QUICK_START.md`

2. **Complete Documentation**:
   - `mcp-server/README_IDE_SETUP.md`

3. **Server Logs**:
   ```bash
   # VSCode
   cat .vscode/mcp.log

   # Zed
   cat .zed/mcp.log

   # Server output (if running manually)
   python -m scheduler_mcp.server
   ```

4. **Test Server Manually**:
   ```bash
   cd mcp-server
   export DATABASE_URL="postgresql://..."
   python -m scheduler_mcp.server
   ```

---

## Usage Examples

### Example 1: Check Schedule Status

**AI Prompt:**
```
Show me the current schedule status for the next 7 days
```

**What Happens:**
1. AI assistant calls `schedule://status` resource
2. Parameters: `start_date=today`, `end_date=today+7`
3. Returns assignments, coverage metrics, and conflicts

### Example 2: Validate ACGME Compliance

**AI Prompt:**
```
Validate the schedule for January 2025 against ACGME work hour rules
```

**What Happens:**
1. AI assistant calls `validate_schedule_tool`
2. Parameters: `start_date=2025-01-01`, `end_date=2025-01-31`
3. Returns validation result with any violations

### Example 3: Analyze Absence Impact

**AI Prompt:**
```
What happens if Dr. Smith is absent from January 15-22?
```

**What Happens:**
1. AI assistant calls `run_contingency_analysis_tool`
2. Parameters: `scenario=faculty_absence`, `affected_person_ids=['smith_id']`
3. Returns impact on coverage, compliance, and suggested resolutions

### Example 4: Find Swap Matches

**AI Prompt:**
```
Find swap candidates for Dr. Johnson's clinic shift on January 20
```

**What Happens:**
1. AI assistant calls `analyze_swap_candidates_tool`
2. Parameters: `requester_person_id='johnson_id'`, `assignment_id=...`
3. Returns ranked list of compatible swap candidates

---

## Integration with Development Workflow

### IDE Features Enabled

#### VSCode
- Python type checking with Pylance
- Automatic formatting with Black
- Linting with Flake8 and MyPy
- TypeScript/React support
- Docker integration
- Git integration with GitLens
- Database tools (SQLTools)

#### Zed
- LSP support for Python (Pyright) and TypeScript
- Automatic formatting
- Git integration with inline blame
- Terminal integration
- Project-wide search

### Recommended Extensions (VSCode)

Already configured in `.vscode/extensions.json`:
- Python development: `ms-python.python`, `ms-python.vscode-pylance`
- Formatting: `ms-python.black-formatter`, `esbenp.prettier-vscode`
- Database: `mtxr.sqltools`, `mtxr.sqltools-driver-pg`
- Git: `eamodio.gitlens`
- Docker: `ms-azuretools.vscode-docker`

---

## Next Steps

### For Developers

1. **Review the full setup guide**: `mcp-server/README_IDE_SETUP.md`
2. **Install MCP server**: `cd mcp-server && pip install -e .`
3. **Configure environment**: Copy and edit `.env` file
4. **Start the server**: Use IDE command palette
5. **Test with AI assistant**: Try querying schedule status

### For System Administrators

1. **Review security considerations** in `README_IDE_SETUP.md`
2. **Create read-only database user** for MCP access
3. **Enable audit logging**: Set `LOG_LEVEL=INFO`
4. **Monitor MCP usage**: Review logs regularly
5. **Implement security controls** as needed

### For AI Assistant Users

1. **Read quick start guide**: `.vscode/MCP_QUICK_START.md` or `.zed/MCP_QUICK_START.md`
2. **Start with simple queries**: Try `schedule://status` first
3. **Explore available tools**: See what analyses are possible
4. **Approve operations carefully**: Review what the AI is doing
5. **Report issues**: Note any unexpected behavior

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-12-18 | Initial release with VSCode and Zed support |

---

## Additional Resources

### Documentation

- **Project README**: `/home/user/Autonomous-Assignment-Program-Manager/README.md`
- **MCP Server README**: `mcp-server/README.md`
- **IDE Setup Guide**: `mcp-server/README_IDE_SETUP.md`
- **Development Guidelines**: `CLAUDE.md`

### External Links

- **MCP Specification**: https://modelcontextprotocol.io/
- **FastMCP Framework**: https://github.com/jlowin/fastmcp
- **ACGME Requirements**: https://www.acgme.org/what-we-do/accreditation/common-program-requirements/

### Support

For issues or questions:
1. Check troubleshooting sections in this document
2. Review `README_IDE_SETUP.md` for detailed help
3. Check server logs for error details
4. Test server manually to isolate issues

---

**Remember**: This is a scheduling system. Security, compliance, and data protection are important. Always follow security best practices and approve operations carefully.
