# Security Scanning Documentation

This document outlines the security scanning practices and tools used in the Residency Scheduler project.

## Overview

Security is critical for healthcare software handling sensitive scheduling and personnel data. This document covers automated security scanning, manual review practices, and remediation procedures.

---

## Automated Security Scanning

### 1. Dependency Vulnerability Scanning

#### Python Dependencies (Backend)

**Tool:** Safety / pip-audit

```bash
# Install safety
pip install safety

# Scan for vulnerabilities
safety check -r backend/requirements.txt

# Alternative: pip-audit
pip install pip-audit
pip-audit -r backend/requirements.txt
```

**CI Integration:** Add to `.github/workflows/security.yml`

#### JavaScript Dependencies (Frontend)

**Tool:** npm audit

```bash
# Run audit
cd frontend && npm audit

# Fix vulnerabilities automatically
npm audit fix

# Fix with breaking changes (review first)
npm audit fix --force
```

**Current Status:** ✅ All vulnerabilities resolved (2025-12-21)

**Resolved Vulnerability:**
- `glob` 10.2.0-10.4.5: Command injection via -c/--cmd (GHSA-5j98-mcp5-4vw2)

**Fix Applied:** npm `overrides` in `frontend/package.json`:
```json
"overrides": {
  "glob": "^10.5.0"
}
```

**Why NOT `npm audit fix --force`:**
Using `npm audit fix --force` upgrades `eslint-config-next` from v14 to v16, which:
1. Requires ESLint v9 (breaking peer dependency change)
2. ESLint v9 uses "flat config" format, incompatible with `next lint` in Next.js 14
3. Causes deployment failures due to config incompatibility

The npm `overrides` approach pins the transitive `glob` dependency to a fixed version
without changing the eslint-config-next major version, avoiding these compatibility issues.

### 2. Static Application Security Testing (SAST)

#### Python SAST - Bandit

```bash
# Install bandit
pip install bandit

# Scan backend code
bandit -r backend/app/ -f json -o bandit-report.json

# Exclude test files
bandit -r backend/app/ --exclude backend/tests/
```

**Common Issues Detected:**
- Hardcoded passwords (B105)
- SQL injection risks (B608)
- Subprocess calls (B602)
- Weak cryptography (B303)

#### TypeScript/JavaScript SAST - ESLint Security Plugins

```bash
# Install security plugins
npm install --save-dev eslint-plugin-security

# Add to eslint config
# "plugins": ["security"]
# "extends": ["plugin:security/recommended"]
```

### 3. Secret Detection

**Tool:** gitleaks / truffleHog

```bash
# Install gitleaks
brew install gitleaks  # macOS
# or download from https://github.com/gitleaks/gitleaks

# Scan repository
gitleaks detect --source . --report-path gitleaks-report.json

# Scan in CI
gitleaks detect --source . --verbose
```

**Patterns to Detect:**
- API keys
- Database credentials
- JWT secrets
- OAuth tokens
- Private keys

### 4. Docker Image Scanning

**Tool:** Trivy

```bash
# Install trivy
brew install trivy  # macOS

# Scan Docker images
trivy image residency-scheduler-backend:latest
trivy image residency-scheduler-frontend:latest

# Scan with severity filter
trivy image --severity HIGH,CRITICAL residency-scheduler-backend:latest
```

---

## Security Checks Performed

### Code Quality Workflow Checks

From `.github/workflows/code-quality.yml`:

1. **Hardcoded Secrets Pattern Check**
   ```bash
   grep -rn --include="*.py" -E \
     "(password|secret|api_key|token)\s*=\s*['\"][^'\"]{8,}['\"]" \
     backend/app/ | grep -v "test\|mock\|example"
   ```

2. **Debug Statement Detection**
   ```bash
   grep -rn "breakpoint()\|pdb\|debugger" backend/app/ frontend/src/
   ```

3. **TODO/FIXME Tracking**
   ```bash
   grep -rn "TODO\|FIXME\|HACK\|XXX" backend/app/ frontend/src/
   ```

---

## Security Configuration

### Environment Variable Security

**Required Secrets (min 32 characters):**
- `SECRET_KEY` - JWT signing key
- `WEBHOOK_SECRET` - Webhook verification
- `DATABASE_URL` - Database connection string

**Validation in Code:**
```python
# backend/app/core/config.py
@validator("SECRET_KEY")
def validate_secret_key(cls, v):
    if len(v) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    return v
```

### CORS Configuration

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Whitelist specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Rate Limiting

```python
# backend/app/main.py
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

---

## OWASP Top 10 Checklist

| Vulnerability | Status | Mitigation |
|---------------|--------|------------|
| A01 Broken Access Control | Implemented | RBAC with 8 roles |
| A02 Cryptographic Failures | Implemented | bcrypt for passwords |
| A03 Injection | Implemented | SQLAlchemy ORM |
| A04 Insecure Design | In Progress | Security review |
| A05 Security Misconfiguration | Implemented | Validated config |
| A06 Vulnerable Components | Monitored | Dependabot enabled |
| A07 Auth Failures | Implemented | JWT + rate limiting |
| A08 Data Integrity | Implemented | Audit logging |
| A09 Security Logging | Implemented | Comprehensive logging |
| A10 SSRF | Mitigated | Input validation |

---

## Vulnerability Response Process

### Severity Levels

| Level | Response Time | Example |
|-------|--------------|---------|
| Critical | 24 hours | RCE, SQL injection |
| High | 72 hours | Auth bypass, XSS |
| Medium | 1 week | Information disclosure |
| Low | 2 weeks | Minor issues |

### Response Steps

1. **Triage** - Assess severity and impact
2. **Isolate** - Contain the vulnerability if active
3. **Patch** - Develop and test fix
4. **Deploy** - Push to production
5. **Verify** - Confirm fix is effective
6. **Document** - Update security docs

---

## Running Security Scans

### Quick Scan (Pre-commit)
```bash
# Run all quick checks
./scripts/pre-deploy-validate.sh
```

### Full Scan (CI/CD)
```bash
# Backend
safety check -r backend/requirements.txt
bandit -r backend/app/

# Frontend
npm audit
npx eslint --ext .ts,.tsx src/ --plugin security

# Docker
trivy image residency-scheduler-backend:latest
trivy image residency-scheduler-frontend:latest

# Secrets
gitleaks detect --source .
```

### Manual Security Review

Quarterly reviews should include:
- [ ] Authentication flow review
- [ ] Authorization matrix verification
- [ ] Data encryption audit
- [ ] API security headers check
- [ ] Third-party dependency review
- [ ] Infrastructure security assessment

---

## Reporting Security Issues

**For internal team:** Create a security issue with `[SECURITY]` prefix

**For external reporters:** Contact security@example.com

**Do NOT:**
- Post security vulnerabilities in public issues
- Share exploit details publicly
- Test on production systems without authorization

---

*Last updated: 2025-12-18*
*Review schedule: Quarterly*
