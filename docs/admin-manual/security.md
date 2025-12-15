# Security Best Practices Guide

## Overview

This guide provides comprehensive security recommendations for deploying and operating the Residency Scheduler application. Given that the system handles sensitive medical scheduling and personnel data, security is paramount.

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Authentication Security](#authentication-security)
3. [Authorization and Access Control](#authorization-and-access-control)
4. [Network Security](#network-security)
5. [Data Protection](#data-protection)
6. [Infrastructure Security](#infrastructure-security)
7. [Application Security](#application-security)
8. [Monitoring and Auditing](#monitoring-and-auditing)
9. [Incident Response](#incident-response)
10. [Compliance Considerations](#compliance-considerations)
11. [Security Checklist](#security-checklist)

---

## Security Architecture

### Defense in Depth

The application implements multiple layers of security:

```
Layer 1: Network Perimeter
├── Firewall rules
├── SSL/TLS encryption
└── Rate limiting

Layer 2: Application Gateway
├── Nginx reverse proxy
├── Security headers
└── Request validation

Layer 3: Application
├── Authentication (JWT)
├── Authorization (RBAC)
├── Input validation
└── Output encoding

Layer 4: Data
├── Encrypted connections
├── Password hashing (bcrypt)
└── Audit logging
```

### Trust Boundaries

| Boundary | Trust Level | Controls |
|----------|-------------|----------|
| Internet | Untrusted | Firewall, WAF, TLS |
| DMZ | Semi-trusted | Reverse proxy, rate limiting |
| Application | Trusted | Auth, RBAC, validation |
| Database | Highly trusted | Connection encryption, least privilege |

---

## Authentication Security

### Password Security

#### Password Hashing

The application uses bcrypt for password hashing:

```python
# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Computational cost factor
)
```

**Bcrypt Configuration:**

| Setting | Value | Reason |
|---------|-------|--------|
| Algorithm | bcrypt | Industry standard, adaptive |
| Rounds | 12 | Balance security/performance |
| Salt | Auto-generated | Unique per password |

#### Password Policy

Enforce strong passwords:

| Requirement | Minimum |
|-------------|---------|
| Length | 12 characters |
| Uppercase | 1 character |
| Lowercase | 1 character |
| Numbers | 1 character |
| Special characters | 1 character |
| Password history | Last 5 passwords |
| Maximum age | 90 days |

### JWT Token Security

#### Token Configuration

```python
# Recommended JWT settings
JWT_SETTINGS = {
    "algorithm": "HS256",
    "access_token_expire_minutes": 15,  # Short-lived
    "refresh_token_expire_days": 7,     # Longer refresh window
}
```

#### Secure Key Generation

```bash
# Generate cryptographically secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Minimum requirements:
# - 256 bits (64 characters base64)
# - Cryptographically random
# - Unique per environment
```

#### Token Storage (Frontend)

**Recommended: HttpOnly PGY2-01ies**

```python
# Backend cookie configuration
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,      # Prevent XSS access
    secure=True,        # HTTPS only
    samesite="lax",     # CSRF protection
    max_age=900,        # 15 minutes
    path="/api"
)
```

### Account Protection

#### Login Attempt Limiting

```python
# Account lockout settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

# Implementation
if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
    if user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=423,
            detail=f"Account locked. Try again after {user.locked_until}"
        )
```

#### Session Management

```python
# Session security practices
SESSION_SETTINGS = {
    "concurrent_sessions": True,       # Allow multiple devices
    "session_timeout_minutes": 60,     # Idle timeout
    "absolute_timeout_hours": 24,      # Maximum session length
    "revoke_on_password_change": True, # Force re-auth on password change
}
```

---

## Authorization and Access Control

### Role-Based Access Control (RBAC)

See [User Management Guide](./user-management.md) for detailed RBAC documentation.

#### Principle of Least Privilege

- Assign minimum necessary permissions
- Use faculty role as default
- Elevate only when required
- Review permissions quarterly

#### Permission Verification

```python
# Always verify permissions at API level
@router.post("/schedules/generate")
async def generate_schedule(
    current_user: User = Depends(require_permission(Permission.SCHEDULES_GENERATE))
):
    """Only users with SCHEDULES_GENERATE can access."""
    pass
```

### Resource-Level Access Control

```python
# Example: Users can only modify their own absences
@router.put("/absences/{absence_id}")
async def update_absence(
    absence_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    absence = db.query(Absence).filter(Absence.id == absence_id).first()

    # Check ownership or elevated permission
    if absence.person_id != current_user.person_id:
        if not has_permission(current_user.role, Permission.ABSENCES_UPDATE_ANY):
            raise HTTPException(status_code=403, detail="Not authorized")
```

---

## Network Security

### Firewall Configuration

#### Recommended Rules (UFW)

```bash
# Reset to defaults
sudo ufw reset

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (restrict to specific IPs in production)
sudo ufw allow from 10.0.0.0/8 to any port 22 proto tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

#### Docker Network Isolation

```yaml
# docker-compose.yml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access

services:
  nginx:
    networks:
      - frontend
      - backend

  backend:
    networks:
      - backend  # Only accessible via nginx

  db:
    networks:
      - backend  # Only accessible from backend
```

### SSL/TLS Configuration

#### Nginx SSL Settings

```nginx
# Modern TLS configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# SSL session configuration
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;
ssl_session_tickets off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;

# HSTS (enable after testing)
add_header Strict-Transport-Security "max-age=63072000" always;
```

#### Certificate Management

```bash
# Use Let's Encrypt for free certificates
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run

# Manual certificate check
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

### Rate Limiting

```nginx
# Define rate limiting zones
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;

# Apply to login endpoint
location /api/auth/login {
    limit_req zone=login burst=10 nodelay;
    proxy_pass http://backend;
}

# Apply to API endpoints
location /api/ {
    limit_req zone=api burst=100 nodelay;
    proxy_pass http://backend;
}
```

---

## Data Protection

### Encryption at Rest

#### Database Encryption

For PostgreSQL, enable encryption:

```bash
# Use encrypted storage volume
# Example: LUKS encryption
sudo cryptsetup luksFormat /dev/sdb
sudo cryptsetup open /dev/sdb encrypted_data
sudo mkfs.ext4 /dev/mapper/encrypted_data
```

#### Backup Encryption

```bash
# Encrypt backups with GPG
pg_dump -U scheduler residency_scheduler | \
  gpg --symmetric --cipher-algo AES256 \
  -o backup_encrypted.sql.gpg

# Decrypt
gpg --decrypt backup_encrypted.sql.gpg > backup.sql
```

### Encryption in Transit

| Connection | Encryption |
|------------|------------|
| Client to Nginx | TLS 1.2/1.3 |
| Nginx to Backend | Internal network (optional TLS) |
| Backend to Database | SSL required |

#### PostgreSQL SSL

```ini
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/postgresql/server.crt'
ssl_key_file = '/etc/postgresql/server.key'
```

```bash
# Connection string with SSL
DATABASE_URL=postgresql://scheduler:password@localhost:5432/residency_scheduler?sslmode=require
```

### Sensitive Data Handling

#### Data Classification

| Classification | Examples | Handling |
|----------------|----------|----------|
| Public | Schedule summaries | Standard controls |
| Internal | Staff names, emails | Access control |
| Confidential | Medical leave reasons | Encryption, audit |
| Restricted | Passwords, tokens | Never logged, encrypted |

#### Data Masking in Logs

```python
# Never log sensitive data
logger.info(f"User {user.id} logged in")  # Good
logger.info(f"User {user.id} with password {password}")  # BAD!

# Mask sensitive fields in error responses
def sanitize_error(error: dict) -> dict:
    sensitive_fields = ['password', 'token', 'secret', 'key']
    return {k: '***' if k in sensitive_fields else v for k, v in error.items()}
```

---

## Infrastructure Security

### Server Hardening

#### Operating System

```bash
# Keep system updated
sudo apt update && sudo apt upgrade -y

# Enable automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Disable root login
sudo passwd -l root

# Configure SSH
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
```

#### Docker Security

```bash
# Run containers as non-root
# In Dockerfile:
USER nonroot

# Limit container capabilities
# In docker-compose.yml:
services:
  backend:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    security_opt:
      - no-new-privileges:true
```

### Secret Management

#### Environment Variables

```bash
# Store secrets in environment, not code
export SECRET_KEY="your-secret-key"

# Use .env file with restricted permissions
chmod 600 .env
```

#### Recommended: External Secret Manager

```bash
# HashiCorp Vault example
vault kv put secret/residency-scheduler \
  db_password="..." \
  secret_key="..."

# Retrieve at runtime
vault kv get -field=secret_key secret/residency-scheduler
```

### Container Registry Security

```bash
# Scan images for vulnerabilities
docker scan residency-scheduler-backend

# Use specific image versions (not :latest)
image: postgres:15-alpine

# Sign images
docker trust sign your-registry/residency-scheduler:1.0
```

---

## Application Security

### Input Validation

#### Pydantic Schema Validation

```python
from pydantic import BaseModel, Field, EmailStr, validator

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=12)

    @validator('password')
    def validate_password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

### SQL Injection Prevention

```python
# Use SQLAlchemy ORM (safe)
user = db.query(User).filter(User.username == username).first()

# NEVER use string formatting (unsafe)
# db.execute(f"SELECT * FROM users WHERE username = '{username}'")  # BAD!
```

### Cross-Site Scripting (XSS) Prevention

```python
# FastAPI auto-escapes JSON responses
# React auto-escapes rendered content

# Additional headers
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["scheduler.hospital.org", "api.scheduler.hospital.org"]
)
```

### Security Headers

```nginx
# Nginx security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
```

### Dependency Security

```bash
# Python: Check for vulnerabilities
pip install safety
safety check -r requirements.txt

# Node.js: Check for vulnerabilities
npm audit
npm audit fix

# Regular updates
pip install --upgrade -r requirements.txt
npm update
```

---

## Monitoring and Auditing

### Security Logging

#### Events to Log

| Event Type | Log Level | Retention |
|------------|-----------|-----------|
| Authentication success | INFO | 90 days |
| Authentication failure | WARNING | 1 year |
| Authorization failure | WARNING | 1 year |
| Data modification | INFO | 7 years |
| Admin actions | INFO | 7 years |
| Security events | CRITICAL | 7 years |

#### Log Format

```python
import structlog

logger = structlog.get_logger()

# Structured logging for security events
logger.info(
    "authentication_success",
    user_id=str(user.id),
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    timestamp=datetime.utcnow().isoformat()
)
```

### Intrusion Detection

#### Monitor for Suspicious Activity

```bash
# Failed login attempts
grep "authentication_failure" /var/log/residency-scheduler/security.log | \
  awk '{print $NF}' | sort | uniq -c | sort -rn | head

# Unusual API patterns
grep "403\|401" /var/log/nginx/access.log | \
  awk '{print $1}' | sort | uniq -c | sort -rn | head
```

### Audit Trail

```python
# All sensitive operations are logged
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    action = Column(String)           # e.g., "schedule.create"
    resource_type = Column(String)    # e.g., "assignment"
    resource_id = Column(UUID)
    changes = Column(JSON)            # {field: {old, new}}
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime)
```

---

## Incident Response

### Incident Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| Critical | Active breach, data loss | Immediate |
| High | Potential breach, vulnerability | 4 hours |
| Medium | Suspicious activity | 24 hours |
| Low | Policy violation | 72 hours |

### Response Procedures

#### Immediate Actions (Critical/High)

1. **Contain:** Isolate affected systems
2. **Assess:** Determine scope and impact
3. **Preserve:** Secure logs and evidence
4. **Notify:** Alert security team and management

```bash
# Emergency: Block all external access
sudo ufw deny from any to any
sudo ufw allow from 10.0.0.0/8  # Internal only
```

#### Investigation Steps

```bash
# Collect logs
docker compose logs --since="2024-12-15T00:00:00" > incident_logs.txt

# Export audit trail
psql -U scheduler -d residency_scheduler -c \
  "COPY (SELECT * FROM audit_logs WHERE created_at > '2024-12-15') TO STDOUT WITH CSV HEADER" \
  > audit_export.csv

# Check for unauthorized access
grep "401\|403\|unauthorized" /var/log/nginx/access.log
```

### Post-Incident

1. Root cause analysis
2. Implement remediation
3. Update security controls
4. Document lessons learned

---

## Compliance Considerations

### HIPAA Considerations

While the Residency Scheduler may not directly store PHI, consider:

- Staff medical leave information may be sensitive
- Implement access controls and audit logging
- Ensure data encryption
- Maintain business associate agreements if applicable

### ACGME Compliance

- Maintain 7-year audit trail for schedule changes
- Ensure data integrity for compliance reporting
- Implement override justification tracking

### General Data Protection

- Minimize data collection
- Implement data retention policies
- Provide data export capability
- Enable account deletion

---

## Security Checklist

### Deployment Security

- [ ] SECRET_KEY is unique and 64+ characters
- [ ] DB_PASSWORD is strong and unique
- [ ] DEBUG mode is disabled
- [ ] HTTPS is enforced
- [ ] Security headers configured
- [ ] Firewall rules implemented
- [ ] Rate limiting enabled

### Authentication

- [ ] Password policy enforced
- [ ] Account lockout configured
- [ ] Token expiration appropriate
- [ ] Secure cookie flags set

### Access Control

- [ ] RBAC properly configured
- [ ] Least privilege enforced
- [ ] Resource-level checks implemented

### Data Protection

- [ ] Database connections encrypted
- [ ] Backups encrypted
- [ ] Sensitive data not logged
- [ ] Audit logging enabled

### Infrastructure

- [ ] OS updated and hardened
- [ ] SSH key-only authentication
- [ ] Docker security best practices
- [ ] Vulnerability scanning enabled

### Monitoring

- [ ] Security logging configured
- [ ] Log retention appropriate
- [ ] Alerting configured
- [ ] Regular log review scheduled

### Ongoing

- [ ] Regular dependency updates
- [ ] Quarterly access reviews
- [ ] Annual security assessment
- [ ] Incident response plan tested

---

*Last Updated: December 2024*
