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

See [Configuration Guide](../getting-started/configuration.md) for security settings.
