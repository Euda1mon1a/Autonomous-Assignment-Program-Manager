# Configuration

Advanced system configuration options.

---

## Application Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Academic Year Start | First day of academic year | July 1 |
| Block Duration | Hours per block | 12 |
| Max PGY-1 Ratio | Faculty supervision | 1:2 |
| Max PGY-2/3 Ratio | Faculty supervision | 1:4 |

---

## Email Configuration

Configure SMTP for notifications:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=notifications@example.com
SMTP_PASSWORD=your_password
SMTP_FROM=Residency Scheduler <noreply@example.com>
```

---

## Resilience Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Utilization Warning | Warning threshold | 75% |
| Utilization Critical | Critical threshold | 85% |
| Contingency Check | Analysis frequency | 4 hours |

---

## Security Settings

### Rate Limiting

The application includes sliding window rate limiting to prevent brute force attacks:

| Setting | Description | Default |
|---------|-------------|---------|
| `RATE_LIMIT_LOGIN_ATTEMPTS` | Max login attempts per minute | 5 |
| `RATE_LIMIT_LOGIN_WINDOW` | Login rate limit window (seconds) | 60 |
| `RATE_LIMIT_REGISTER_ATTEMPTS` | Max registration attempts per minute | 3 |
| `RATE_LIMIT_REGISTER_WINDOW` | Registration rate limit window (seconds) | 60 |
| `RATE_LIMIT_ENABLED` | Enable/disable rate limiting globally | true |

### Trusted Proxies

When running behind a load balancer or reverse proxy, configure trusted proxies to ensure
rate limiting uses the correct client IP from the `X-Forwarded-For` header:

```env
# Only trust X-Forwarded-For from these IPs
TRUSTED_PROXIES=["10.0.0.1", "172.16.0.0/12"]
```

| Setting | Description | Default |
|---------|-------------|---------|
| `TRUSTED_PROXIES` | List of trusted proxy IPs or CIDR ranges | `[]` (empty - uses direct client IP) |

**Security Note:** If `TRUSTED_PROXIES` is empty (default), the application uses the direct
client IP and ignores `X-Forwarded-For` headers. This prevents rate limit bypass via header
spoofing when not running behind a trusted proxy.

### Additional Security Settings

See [Configuration Guide](../getting-started/configuration.md) for additional security settings.
