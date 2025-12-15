***REMOVED*** Security Best Practices Guide

***REMOVED******REMOVED*** Overview

This guide provides comprehensive security recommendations for deploying and operating the Residency Scheduler application. Given that the system handles sensitive medical scheduling and personnel data, security is paramount.

***REMOVED******REMOVED*** Table of Contents

1. [Security Architecture](***REMOVED***security-architecture)
2. [Authentication Security](***REMOVED***authentication-security)
3. [Authorization and Access Control](***REMOVED***authorization-and-access-control)
4. [Network Security](***REMOVED***network-security)
5. [Data Protection](***REMOVED***data-protection)
6. [Infrastructure Security](***REMOVED***infrastructure-security)
7. [Application Security](***REMOVED***application-security)
8. [Monitoring and Auditing](***REMOVED***monitoring-and-auditing)
9. [Incident Response](***REMOVED***incident-response)
10. [Compliance Considerations](***REMOVED***compliance-considerations)
11. [Security Checklist](***REMOVED***security-checklist)

---

***REMOVED******REMOVED*** Security Architecture

***REMOVED******REMOVED******REMOVED*** Defense in Depth

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

***REMOVED******REMOVED******REMOVED*** Trust Boundaries

| Boundary | Trust Level | Controls |
|----------|-------------|----------|
| Internet | Untrusted | Firewall, WAF, TLS |
| DMZ | Semi-trusted | Reverse proxy, rate limiting |
| Application | Trusted | Auth, RBAC, validation |
| Database | Highly trusted | Connection encryption, least privilege |

---

***REMOVED******REMOVED*** Authentication Security

***REMOVED******REMOVED******REMOVED*** Password Security

***REMOVED******REMOVED******REMOVED******REMOVED*** Password Hashing

The application uses bcrypt for password hashing:

```python
***REMOVED*** Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  ***REMOVED*** Computational cost factor
)
```

**Bcrypt Configuration:**

| Setting | Value | Reason |
|---------|-------|--------|
| Algorithm | bcrypt | Industry standard, adaptive |
| Rounds | 12 | Balance security/performance |
| Salt | Auto-generated | Unique per password |

***REMOVED******REMOVED******REMOVED******REMOVED*** Password Policy

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

***REMOVED******REMOVED******REMOVED*** JWT Token Security

***REMOVED******REMOVED******REMOVED******REMOVED*** Token Configuration

```python
***REMOVED*** Recommended JWT settings
JWT_SETTINGS = {
    "algorithm": "HS256",
    "access_token_expire_minutes": 15,  ***REMOVED*** Short-lived
    "refresh_token_expire_days": 7,     ***REMOVED*** Longer refresh window
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Secure Key Generation

```bash
***REMOVED*** Generate cryptographically secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

***REMOVED*** Minimum requirements:
***REMOVED*** - 256 bits (64 characters base64)
***REMOVED*** - Cryptographically random
***REMOVED*** - Unique per environment
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Token Storage (Frontend)

**Recommended: HttpOnly PGY2-01ies**

```python
***REMOVED*** Backend cookie configuration
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,      ***REMOVED*** Prevent XSS access
    secure=True,        ***REMOVED*** HTTPS only
    samesite="lax",     ***REMOVED*** CSRF protection
    max_age=900,        ***REMOVED*** 15 minutes
    path="/api"
)
```

***REMOVED******REMOVED******REMOVED*** Account Protection

***REMOVED******REMOVED******REMOVED******REMOVED*** Login Attempt Limiting

```python
***REMOVED*** Account lockout settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

***REMOVED*** Implementation
if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
    if user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=423,
            detail=f"Account locked. Try again after {user.locked_until}"
        )
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Session Management

```python
***REMOVED*** Session security practices
SESSION_SETTINGS = {
    "concurrent_sessions": True,       ***REMOVED*** Allow multiple devices
    "session_timeout_minutes": 60,     ***REMOVED*** Idle timeout
    "absolute_timeout_hours": 24,      ***REMOVED*** Maximum session length
    "revoke_on_password_change": True, ***REMOVED*** Force re-auth on password change
}
```

---

***REMOVED******REMOVED*** Authorization and Access Control

***REMOVED******REMOVED******REMOVED*** Role-Based Access Control (RBAC)

See [User Management Guide](./user-management.md) for detailed RBAC documentation.

***REMOVED******REMOVED******REMOVED******REMOVED*** Principle of Least Privilege

- Assign minimum necessary permissions
- Use faculty role as default
- Elevate only when required
- Review permissions quarterly

***REMOVED******REMOVED******REMOVED******REMOVED*** Permission Verification

```python
***REMOVED*** Always verify permissions at API level
@router.post("/schedules/generate")
async def generate_schedule(
    current_user: User = Depends(require_permission(Permission.SCHEDULES_GENERATE))
):
    """Only users with SCHEDULES_GENERATE can access."""
    pass
```

***REMOVED******REMOVED******REMOVED*** Resource-Level Access Control

```python
***REMOVED*** Example: Users can only modify their own absences
@router.put("/absences/{absence_id}")
async def update_absence(
    absence_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    absence = db.query(Absence).filter(Absence.id == absence_id).first()

    ***REMOVED*** Check ownership or elevated permission
    if absence.person_id != current_user.person_id:
        if not has_permission(current_user.role, Permission.ABSENCES_UPDATE_ANY):
            raise HTTPException(status_code=403, detail="Not authorized")
```

---

***REMOVED******REMOVED*** Network Security

***REMOVED******REMOVED******REMOVED*** Firewall Configuration

***REMOVED******REMOVED******REMOVED******REMOVED*** Recommended Rules (UFW)

```bash
***REMOVED*** Reset to defaults
sudo ufw reset

***REMOVED*** Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

***REMOVED*** Allow SSH (restrict to specific IPs in production)
sudo ufw allow from 10.0.0.0/8 to any port 22 proto tcp

***REMOVED*** Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

***REMOVED*** Enable firewall
sudo ufw enable
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Docker Network Isolation

```yaml
***REMOVED*** docker-compose.yml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  ***REMOVED*** No external access

services:
  nginx:
    networks:
      - frontend
      - backend

  backend:
    networks:
      - backend  ***REMOVED*** Only accessible via nginx

  db:
    networks:
      - backend  ***REMOVED*** Only accessible from backend
```

***REMOVED******REMOVED******REMOVED*** SSL/TLS Configuration

***REMOVED******REMOVED******REMOVED******REMOVED*** Nginx SSL Settings

```nginx
***REMOVED*** Modern TLS configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

***REMOVED*** SSL session configuration
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;
ssl_session_tickets off;

***REMOVED*** OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;

***REMOVED*** HSTS (enable after testing)
add_header Strict-Transport-Security "max-age=63072000" always;
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Certificate Management

```bash
***REMOVED*** Use Let's Encrypt for free certificates
sudo certbot --nginx -d your-domain.com

***REMOVED*** Auto-renewal
sudo certbot renew --dry-run

***REMOVED*** Manual certificate check
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

***REMOVED******REMOVED******REMOVED*** Rate Limiting

```nginx
***REMOVED*** Define rate limiting zones
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;

***REMOVED*** Apply to login endpoint
location /api/auth/login {
    limit_req zone=login burst=10 nodelay;
    proxy_pass http://backend;
}

***REMOVED*** Apply to API endpoints
location /api/ {
    limit_req zone=api burst=100 nodelay;
    proxy_pass http://backend;
}
```

---

***REMOVED******REMOVED*** Data Protection

***REMOVED******REMOVED******REMOVED*** Encryption at Rest

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Encryption

For PostgreSQL, enable encryption:

```bash
***REMOVED*** Use encrypted storage volume
***REMOVED*** Example: LUKS encryption
sudo cryptsetup luksFormat /dev/sdb
sudo cryptsetup open /dev/sdb encrypted_data
sudo mkfs.ext4 /dev/mapper/encrypted_data
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Backup Encryption

```bash
***REMOVED*** Encrypt backups with GPG
pg_dump -U scheduler residency_scheduler | \
  gpg --symmetric --cipher-algo AES256 \
  -o backup_encrypted.sql.gpg

***REMOVED*** Decrypt
gpg --decrypt backup_encrypted.sql.gpg > backup.sql
```

***REMOVED******REMOVED******REMOVED*** Encryption in Transit

| Connection | Encryption |
|------------|------------|
| Client to Nginx | TLS 1.2/1.3 |
| Nginx to Backend | Internal network (optional TLS) |
| Backend to Database | SSL required |

***REMOVED******REMOVED******REMOVED******REMOVED*** PostgreSQL SSL

```ini
***REMOVED*** postgresql.conf
ssl = on
ssl_cert_file = '/etc/postgresql/server.crt'
ssl_key_file = '/etc/postgresql/server.key'
```

```bash
***REMOVED*** Connection string with SSL
DATABASE_URL=postgresql://scheduler:password@localhost:5432/residency_scheduler?sslmode=require
```

***REMOVED******REMOVED******REMOVED*** Sensitive Data Handling

***REMOVED******REMOVED******REMOVED******REMOVED*** Data Classification

| Classification | Examples | Handling |
|----------------|----------|----------|
| Public | Schedule summaries | Standard controls |
| Internal | Staff names, emails | Access control |
| Confidential | Medical leave reasons | Encryption, audit |
| Restricted | Passwords, tokens | Never logged, encrypted |

***REMOVED******REMOVED******REMOVED******REMOVED*** Data Masking in Logs

```python
***REMOVED*** Never log sensitive data
logger.info(f"User {user.id} logged in")  ***REMOVED*** Good
logger.info(f"User {user.id} with password {password}")  ***REMOVED*** BAD!

***REMOVED*** Mask sensitive fields in error responses
def sanitize_error(error: dict) -> dict:
    sensitive_fields = ['password', 'token', 'secret', 'key']
    return {k: '***' if k in sensitive_fields else v for k, v in error.items()}
```

---

***REMOVED******REMOVED*** Infrastructure Security

***REMOVED******REMOVED******REMOVED*** Server Hardening

***REMOVED******REMOVED******REMOVED******REMOVED*** Operating System

```bash
***REMOVED*** Keep system updated
sudo apt update && sudo apt upgrade -y

***REMOVED*** Enable automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

***REMOVED*** Disable root login
sudo passwd -l root

***REMOVED*** Configure SSH
sudo nano /etc/ssh/sshd_config
***REMOVED*** PermitRootLogin no
***REMOVED*** PasswordAuthentication no
***REMOVED*** PubkeyAuthentication yes
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Docker Security

```bash
***REMOVED*** Run containers as non-root
***REMOVED*** In Dockerfile:
USER nonroot

***REMOVED*** Limit container capabilities
***REMOVED*** In docker-compose.yml:
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

***REMOVED******REMOVED******REMOVED*** Secret Management

***REMOVED******REMOVED******REMOVED******REMOVED*** Environment Variables

```bash
***REMOVED*** Store secrets in environment, not code
export SECRET_KEY="your-secret-key"

***REMOVED*** Use .env file with restricted permissions
chmod 600 .env
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Recommended: External Secret Manager

```bash
***REMOVED*** HashiCorp Vault example
vault kv put secret/residency-scheduler \
  db_password="..." \
  secret_key="..."

***REMOVED*** Retrieve at runtime
vault kv get -field=secret_key secret/residency-scheduler
```

***REMOVED******REMOVED******REMOVED*** Container Registry Security

```bash
***REMOVED*** Scan images for vulnerabilities
docker scan residency-scheduler-backend

***REMOVED*** Use specific image versions (not :latest)
image: postgres:15-alpine

***REMOVED*** Sign images
docker trust sign your-registry/residency-scheduler:1.0
```

---

***REMOVED******REMOVED*** Application Security

***REMOVED******REMOVED******REMOVED*** Input Validation

***REMOVED******REMOVED******REMOVED******REMOVED*** Pydantic Schema Validation

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

***REMOVED******REMOVED******REMOVED*** SQL Injection Prevention

```python
***REMOVED*** Use SQLAlchemy ORM (safe)
user = db.query(User).filter(User.username == username).first()

***REMOVED*** NEVER use string formatting (unsafe)
***REMOVED*** db.execute(f"SELECT * FROM users WHERE username = '{username}'")  ***REMOVED*** BAD!
```

***REMOVED******REMOVED******REMOVED*** Cross-Site Scripting (XSS) Prevention

```python
***REMOVED*** FastAPI auto-escapes JSON responses
***REMOVED*** React auto-escapes rendered content

***REMOVED*** Additional headers
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["scheduler.hospital.org", "api.scheduler.hospital.org"]
)
```

***REMOVED******REMOVED******REMOVED*** Security Headers

```nginx
***REMOVED*** Nginx security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
```

***REMOVED******REMOVED******REMOVED*** Dependency Security

```bash
***REMOVED*** Python: Check for vulnerabilities
pip install safety
safety check -r requirements.txt

***REMOVED*** Node.js: Check for vulnerabilities
npm audit
npm audit fix

***REMOVED*** Regular updates
pip install --upgrade -r requirements.txt
npm update
```

---

***REMOVED******REMOVED*** Monitoring and Auditing

***REMOVED******REMOVED******REMOVED*** Security Logging

***REMOVED******REMOVED******REMOVED******REMOVED*** Events to Log

| Event Type | Log Level | Retention |
|------------|-----------|-----------|
| Authentication success | INFO | 90 days |
| Authentication failure | WARNING | 1 year |
| Authorization failure | WARNING | 1 year |
| Data modification | INFO | 7 years |
| Admin actions | INFO | 7 years |
| Security events | CRITICAL | 7 years |

***REMOVED******REMOVED******REMOVED******REMOVED*** Log Format

```python
import structlog

logger = structlog.get_logger()

***REMOVED*** Structured logging for security events
logger.info(
    "authentication_success",
    user_id=str(user.id),
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    timestamp=datetime.utcnow().isoformat()
)
```

***REMOVED******REMOVED******REMOVED*** Intrusion Detection

***REMOVED******REMOVED******REMOVED******REMOVED*** Monitor for Suspicious Activity

```bash
***REMOVED*** Failed login attempts
grep "authentication_failure" /var/log/residency-scheduler/security.log | \
  awk '{print $NF}' | sort | uniq -c | sort -rn | head

***REMOVED*** Unusual API patterns
grep "403\|401" /var/log/nginx/access.log | \
  awk '{print $1}' | sort | uniq -c | sort -rn | head
```

***REMOVED******REMOVED******REMOVED*** Audit Trail

```python
***REMOVED*** All sensitive operations are logged
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    action = Column(String)           ***REMOVED*** e.g., "schedule.create"
    resource_type = Column(String)    ***REMOVED*** e.g., "assignment"
    resource_id = Column(UUID)
    changes = Column(JSON)            ***REMOVED*** {field: {old, new}}
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime)
```

---

***REMOVED******REMOVED*** Incident Response

***REMOVED******REMOVED******REMOVED*** Incident Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| Critical | Active breach, data loss | Immediate |
| High | Potential breach, vulnerability | 4 hours |
| Medium | Suspicious activity | 24 hours |
| Low | Policy violation | 72 hours |

***REMOVED******REMOVED******REMOVED*** Response Procedures

***REMOVED******REMOVED******REMOVED******REMOVED*** Immediate Actions (Critical/High)

1. **Contain:** Isolate affected systems
2. **Assess:** Determine scope and impact
3. **Preserve:** Secure logs and evidence
4. **Notify:** Alert security team and management

```bash
***REMOVED*** Emergency: Block all external access
sudo ufw deny from any to any
sudo ufw allow from 10.0.0.0/8  ***REMOVED*** Internal only
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Investigation Steps

```bash
***REMOVED*** Collect logs
docker compose logs --since="2024-12-15T00:00:00" > incident_logs.txt

***REMOVED*** Export audit trail
psql -U scheduler -d residency_scheduler -c \
  "COPY (SELECT * FROM audit_logs WHERE created_at > '2024-12-15') TO STDOUT WITH CSV HEADER" \
  > audit_export.csv

***REMOVED*** Check for unauthorized access
grep "401\|403\|unauthorized" /var/log/nginx/access.log
```

***REMOVED******REMOVED******REMOVED*** Post-Incident

1. Root cause analysis
2. Implement remediation
3. Update security controls
4. Document lessons learned

---

***REMOVED******REMOVED*** Compliance Considerations

***REMOVED******REMOVED******REMOVED*** HIPAA Considerations

While the Residency Scheduler may not directly store PHI, consider:

- Staff medical leave information may be sensitive
- Implement access controls and audit logging
- Ensure data encryption
- Maintain business associate agreements if applicable

***REMOVED******REMOVED******REMOVED*** ACGME Compliance

- Maintain 7-year audit trail for schedule changes
- Ensure data integrity for compliance reporting
- Implement override justification tracking

***REMOVED******REMOVED******REMOVED*** General Data Protection

- Minimize data collection
- Implement data retention policies
- Provide data export capability
- Enable account deletion

---

***REMOVED******REMOVED*** Security Checklist

***REMOVED******REMOVED******REMOVED*** Deployment Security

- [ ] SECRET_KEY is unique and 64+ characters
- [ ] DB_PASSWORD is strong and unique
- [ ] DEBUG mode is disabled
- [ ] HTTPS is enforced
- [ ] Security headers configured
- [ ] Firewall rules implemented
- [ ] Rate limiting enabled

***REMOVED******REMOVED******REMOVED*** Authentication

- [ ] Password policy enforced
- [ ] Account lockout configured
- [ ] Token expiration appropriate
- [ ] Secure cookie flags set

***REMOVED******REMOVED******REMOVED*** Access Control

- [ ] RBAC properly configured
- [ ] Least privilege enforced
- [ ] Resource-level checks implemented

***REMOVED******REMOVED******REMOVED*** Data Protection

- [ ] Database connections encrypted
- [ ] Backups encrypted
- [ ] Sensitive data not logged
- [ ] Audit logging enabled

***REMOVED******REMOVED******REMOVED*** Infrastructure

- [ ] OS updated and hardened
- [ ] SSH key-only authentication
- [ ] Docker security best practices
- [ ] Vulnerability scanning enabled

***REMOVED******REMOVED******REMOVED*** Monitoring

- [ ] Security logging configured
- [ ] Log retention appropriate
- [ ] Alerting configured
- [ ] Regular log review scheduled

***REMOVED******REMOVED******REMOVED*** Ongoing

- [ ] Regular dependency updates
- [ ] Quarterly access reviews
- [ ] Annual security assessment
- [ ] Incident response plan tested

---

*Last Updated: December 2024*
