# Deployment Workflow Automation Tools

GitOps-style deployment automation via MCP for the Residency Scheduler.

## Overview

The deployment tools enable AI assistants to orchestrate deployments through Model Context Protocol (MCP). These tools integrate with GitHub Actions to provide secure, audited, and validated deployment workflows.

## Available Tools

### 1. `validate_deployment`

Validates a deployment before execution.

**Parameters:**
- `environment`: `"staging"` or `"production"`
- `git_ref`: Git reference to deploy (branch, tag, or SHA)
- `dry_run`: Simulate validation without side effects (default: `false`)
- `skip_tests`: Skip test verification - not recommended (default: `false`)
- `skip_security_scan`: Skip security scan - not recommended (default: `false`)

**Returns:**
```python
{
    "valid": bool,
    "environment": "staging" | "production",
    "git_ref": str,
    "checks": [
        {
            "check_name": str,
            "status": "passed" | "failed" | "skipped" | "warning",
            "message": str,
            "details": dict,
            "duration_ms": int
        }
    ],
    "blockers": [str],
    "warnings": [str],
    "validated_at": datetime,
    "validation_duration_ms": int
}
```

**Example:**
```python
result = await validate_deployment_tool(
    environment="staging",
    git_ref="main",
    dry_run=False
)

if result.valid:
    print("✓ Deployment is ready!")
else:
    print(f"✗ Blockers: {result.blockers}")
```

---

### 2. `run_security_scan`

Runs comprehensive security scanning.

**Parameters:**
- `git_ref`: Git reference to scan
- `scan_dependencies`: Run dependency vulnerability scan (default: `true`)
- `scan_code`: Run SAST analysis (default: `true`)
- `scan_secrets`: Run secret detection (default: `true`)
- `dry_run`: Simulate scan (default: `false`)

**Returns:**
```python
{
    "git_ref": str,
    "vulnerabilities": [
        {
            "id": str,
            "title": str,
            "severity": "critical" | "high" | "medium" | "low" | "info",
            "package": str,
            "affected_versions": str,
            "fixed_version": str,
            "description": str,
            "cvss_score": float,
            "references": [str]
        }
    ],
    "severity_summary": {
        "critical": int,
        "high": int,
        "medium": int,
        "low": int,
        "info": int
    },
    "passed": bool,
    "scan_duration_ms": int,
    "scanned_at": datetime,
    "blockers": [str]
}
```

**Example:**
```python
result = await run_security_scan_tool(
    git_ref="main",
    dry_run=False
)

if result.severity_summary.get("critical", 0) > 0:
    print(f"⚠ Critical vulnerabilities found!")
```

---

### 3. `run_smoke_tests`

Executes smoke tests against deployed environment.

**Parameters:**
- `environment`: `"staging"` or `"production"`
- `test_suite`: `"basic"` or `"full"` (default: `"basic"`)
- `timeout_seconds`: Test timeout in seconds, 30-1800 (default: `300`)
- `dry_run`: Simulate tests (default: `false`)

**Returns:**
```python
{
    "environment": "staging" | "production",
    "test_suite": "basic" | "full",
    "passed": bool,
    "results": [
        {
            "check_name": str,
            "status": "passed" | "failed",
            "message": str,
            "details": dict,
            "duration_ms": int
        }
    ],
    "duration_ms": int,
    "executed_at": datetime
}
```

**Example:**
```python
result = await run_smoke_tests_tool(
    environment="staging",
    test_suite="full",
    dry_run=False
)

if result.passed:
    print("✓ All smoke tests passed!")
else:
    failed = [r for r in result.results if r.status == "failed"]
    print(f"✗ {len(failed)} tests failed")
```

---

### 4. `promote_to_production`

Promotes staging deployment to production.

**Parameters:**
- `staging_version`: Staging version to promote (git ref)
- `approval_token`: Human approval token for production deployment
- `skip_smoke_tests`: Skip smoke test verification - not recommended (default: `false`)
- `dry_run`: Simulate promotion (default: `false`)

**Returns:**
```python
{
    "status": "queued" | "in_progress" | "success" | "failure",
    "deployment_id": str,
    "staging_version": str,
    "production_version": str,
    "initiated_at": datetime,
    "estimated_duration_minutes": int
}
```

**Example:**
```python
result = await promote_to_production_tool(
    staging_version="v1.2.3",
    approval_token="prod-token-abc123",
    dry_run=False
)

print(f"Deployment ID: {result.deployment_id}")
print(f"Status: {result.status}")
```

**Security:**
Production deployments require valid approval token. Set `DEPLOYMENT_ADMIN_TOKENS` environment variable.

---

### 5. `rollback_deployment`

Rolls back a deployment to previous version.

**Parameters:**
- `environment`: `"staging"` or `"production"`
- `reason`: Reason for rollback (for audit trail)
- `target_version`: Optional specific version to rollback to
- `dry_run`: Simulate rollback (default: `false`)

**Returns:**
```python
{
    "status": "rolling_back",
    "environment": "staging" | "production",
    "from_version": str,
    "to_version": str,
    "rollback_id": str,
    "initiated_at": datetime
}
```

**Example:**
```python
result = await rollback_deployment_tool(
    environment="production",
    reason="Critical bug in authentication",
    dry_run=False
)

print(f"Rolling back from {result.from_version} to {result.to_version}")
```

**Note:**
If `target_version` is not specified, rolls back to most recent successful deployment.

---

### 6. `get_deployment_status`

Retrieves current status of a deployment.

**Parameters:**
- `deployment_id`: Deployment identifier

**Returns:**
```python
{
    "deployment": {
        "deployment_id": str,
        "environment": "staging" | "production",
        "status": "queued" | "in_progress" | "success" | "failure",
        "version": str,
        "git_ref": str,
        "initiated_by": str,
        "initiated_at": datetime,
        "completed_at": datetime,
        "duration_ms": int,
        "health_status": str,
        "logs_url": str
    },
    "checks": [DeploymentCheck],
    "logs": [str],
    "health_checks": {
        "api": str,
        "database": str,
        "redis": str,
        "celery_worker": str,
        "celery_beat": str
    }
}
```

**Example:**
```python
result = await get_deployment_status_tool(
    deployment_id="deploy-1234567890.123"
)

print(f"Status: {result.deployment.status}")
print(f"Health: {result.health_checks}")

for log in result.logs:
    print(log)
```

---

### 7. `list_deployments`

Lists recent deployments.

**Parameters:**
- `environment`: Filter by environment (optional)
- `limit`: Maximum number to return, 1-100 (default: `10`)
- `include_failed`: Include failed deployments (default: `true`)

**Returns:**
```python
{
    "deployments": [DeploymentInfo],
    "total_count": int,
    "retrieved_at": datetime
}
```

**Example:**
```python
result = await list_deployments_tool(
    environment="production",
    limit=5,
    include_failed=False
)

for deployment in result.deployments:
    print(f"{deployment.version}: {deployment.status}")
```

---

## Environment Variables

### Required

- **`GITHUB_TOKEN`**: GitHub personal access token with workflow permissions
- **`GITHUB_REPOSITORY`**: Repository in format `owner/repo`

### Optional

- **`STAGING_URL`**: Staging environment URL (for smoke tests)
  - Default: `https://staging.scheduler.example.com`

- **`PRODUCTION_URL`**: Production environment URL (for smoke tests)
  - Default: `https://scheduler.example.com`

- **`DEPLOYMENT_ADMIN_TOKENS`**: Comma-separated list of admin tokens for production deployments
  - Example: `token1,token2,token3`

- **`DEPLOYMENT_AUDIT_LOG`**: Path to audit log file
  - Default: `/var/log/scheduler/deployments.log`

### Setting Environment Variables

```bash
# Development
export GITHUB_TOKEN="ghp_..."
export GITHUB_REPOSITORY="yourusername/autonomous-assignment-program-manager"
export STAGING_URL="https://staging.scheduler.example.com"
export DEPLOYMENT_ADMIN_TOKENS="your-secure-token-here"

# Production (use secrets management)
# Store in GitHub Secrets, AWS Secrets Manager, or similar
```

---

## GitHub Actions Integration

The tools integrate with the existing CD workflow at `.github/workflows/cd.yml`.

### Workflow Dispatch

Tools trigger workflows using the GitHub Actions API:

```python
# Internally calls:
POST /repos/{owner}/{repo}/actions/workflows/cd.yml/dispatches
{
    "ref": "main",
    "inputs": {
        "environment": "production",
        "skip_tests": "false"
    }
}
```

### Permissions Required

GitHub token needs these permissions:
- `actions:write` - Trigger workflows
- `contents:read` - Read repository content
- `deployments:write` - Create deployment records

---

## Security Features

### 1. **Audit Logging**

All deployment operations are logged:

```python
{
    "timestamp": "2025-01-15T10:30:00Z",
    "operation": "promote_to_production",
    "user": "token-hash-abc123",
    "environment": "production",
    "success": true,
    "details": {
        "staging_version": "v1.2.3",
        "deployment_id": "deploy-123456789.0"
    }
}
```

### 2. **Permission Checking**

Production deployments require approval tokens:

```python
class PermissionChecker:
    def check_permission(operation, environment, token):
        # Production operations require admin token
        if environment == Environment.PRODUCTION:
            if token not in self.admin_tokens:
                return False
        return True
```

### 3. **Token Hashing**

Tokens are hashed before logging:

```python
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:12]
```

### 4. **Dry-Run Mode**

All tools support dry-run for testing:

```python
result = await validate_deployment_tool(
    environment="production",
    git_ref="v1.2.3",
    dry_run=True  # Simulate without side effects
)
```

---

## Usage Patterns

### Standard Deployment Flow

```python
# 1. Validate deployment
validation = await validate_deployment_tool(
    environment="staging",
    git_ref="main"
)

if not validation.valid:
    raise Exception(f"Validation failed: {validation.blockers}")

# 2. Run security scan
scan = await run_security_scan_tool(git_ref="main")

if scan.severity_summary.get("critical", 0) > 0:
    raise Exception("Critical vulnerabilities detected!")

# 3. Deploy to staging (handled by GitHub Actions)

# 4. Run smoke tests
smoke = await run_smoke_tests_tool(
    environment="staging",
    test_suite="full"
)

if not smoke.passed:
    raise Exception("Smoke tests failed!")

# 5. Promote to production
deployment = await promote_to_production_tool(
    staging_version="main",
    approval_token=os.getenv("PROD_APPROVAL_TOKEN")
)

# 6. Monitor deployment
status = await get_deployment_status_tool(
    deployment_id=deployment.deployment_id
)

print(f"Deployment status: {status.deployment.status}")
```

### Emergency Rollback

```python
# List recent deployments
deployments = await list_deployments_tool(
    environment="production",
    limit=5,
    include_failed=True
)

print("Recent deployments:")
for d in deployments.deployments:
    print(f"  {d.version}: {d.status}")

# Rollback to previous version
rollback = await rollback_deployment_tool(
    environment="production",
    reason="Critical bug detected in production"
)

print(f"Rolling back from {rollback.from_version} to {rollback.to_version}")
```

---

## Error Handling

All tools raise exceptions for invalid inputs:

```python
try:
    result = await validate_deployment_tool(
        environment="invalid",  # Not "staging" or "production"
        git_ref="main"
    )
except ValueError as e:
    print(f"Error: {e}")
    # Output: Invalid environment: invalid. Must be 'staging' or 'production'
```

```python
try:
    result = await promote_to_production_tool(
        staging_version="v1.2.3",
        approval_token="invalid-token"
    )
except PermissionError as e:
    print(f"Error: {e}")
    # Output: Invalid approval token for production deployment
```

---

## Testing

### Unit Tests

```bash
cd mcp-server
pytest tests/test_deployment_tools.py
```

### Integration Tests

```bash
# With actual GitHub Actions
export GITHUB_TOKEN="ghp_..."
export GITHUB_REPOSITORY="owner/repo"

pytest tests/integration/test_deployment_integration.py
```

### Dry-Run Testing

```python
# Test without triggering actual deployments
result = await validate_deployment_tool(
    environment="production",
    git_ref="main",
    dry_run=True
)

assert result.valid == True
```

---

## Monitoring and Observability

### Deployment Metrics

- Deployment frequency
- Lead time for changes
- Mean time to recovery (MTTR)
- Change failure rate

### Health Checks

After deployment, tools verify:
- API health endpoints
- Database connectivity
- Redis connectivity
- Celery worker status
- Celery beat scheduler status

### Logs

Deployment logs are available via:
```python
status = await get_deployment_status_tool(deployment_id)
for log in status.logs:
    print(log)
```

---

## Troubleshooting

### Issue: "GITHUB_TOKEN not set"

**Solution:** Export GitHub token:
```bash
export GITHUB_TOKEN="ghp_..."
```

### Issue: "Invalid approval token for production"

**Solution:** Set admin tokens:
```bash
export DEPLOYMENT_ADMIN_TOKENS="your-token-1,your-token-2"
```

### Issue: "Smoke tests failed"

**Solution:** Check environment URL and health endpoints:
```bash
curl https://staging.scheduler.example.com/api/health
```

### Issue: "Deployment stuck in 'in_progress'"

**Solution:** Check GitHub Actions workflow status:
```bash
gh run list --workflow=cd.yml --limit=1
gh run view <run-id>
```

---

## Best Practices

1. **Always validate before deploying:**
   ```python
   validation = await validate_deployment_tool(...)
   if not validation.valid:
       return
   ```

2. **Run security scans regularly:**
   ```python
   scan = await run_security_scan_tool(git_ref="main")
   ```

3. **Test in staging first:**
   ```python
   # Deploy to staging
   # Run smoke tests
   # Only then promote to production
   ```

4. **Use dry-run for testing:**
   ```python
   result = await promote_to_production_tool(..., dry_run=True)
   ```

5. **Monitor deployments:**
   ```python
   status = await get_deployment_status_tool(deployment_id)
   ```

6. **Keep audit trail:**
   - All operations are automatically logged
   - Review logs regularly

7. **Have rollback plan:**
   ```python
   # Know how to rollback
   rollback = await rollback_deployment_tool(...)
   ```

---

## Architecture

### Components

```
┌─────────────────────────────────────────┐
│         MCP Client (AI Assistant)       │
└───────────────┬─────────────────────────┘
                │
                │ MCP Protocol
                │
┌───────────────▼─────────────────────────┐
│      Scheduler MCP Server               │
│  ┌─────────────────────────────────┐   │
│  │   Deployment Tools              │   │
│  │   - validate_deployment         │   │
│  │   - run_security_scan           │   │
│  │   - run_smoke_tests             │   │
│  │   - promote_to_production       │   │
│  │   - rollback_deployment         │   │
│  │   - get_deployment_status       │   │
│  │   - list_deployments            │   │
│  └──────────┬──────────────────────┘   │
└─────────────┼──────────────────────────┘
              │
              │ GitHub Actions API
              │
┌─────────────▼──────────────────────────┐
│        GitHub Actions                   │
│  ┌──────────────────────────────────┐  │
│  │  CD Workflow (cd.yml)            │  │
│  │  - Build Docker images           │  │
│  │  - Push to registry              │  │
│  │  - Deploy to environment         │  │
│  │  - Run migrations                │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## Future Enhancements

1. **Blue-Green Deployments**
   - Zero-downtime deployments
   - Traffic splitting

2. **Canary Deployments**
   - Gradual rollout
   - Automatic rollback on errors

3. **Deployment Metrics Dashboard**
   - Real-time status
   - Historical trends

4. **Advanced Security Scanning**
   - Container image scanning
   - Runtime vulnerability detection

5. **Automated Rollback**
   - Trigger on health check failures
   - Trigger on error rate thresholds

---

## References

- [GitHub Actions API](https://docs.github.com/en/rest/actions)
- [MCP Specification](https://modelcontextprotocol.io/)
- [GitOps Principles](https://www.gitops.tech/)
- [CD Workflow](.github/workflows/cd.yml)
- [Pre-Deploy Validation](scripts/pre-deploy-validate.sh)

---

*Last updated: 2025-01-15*
