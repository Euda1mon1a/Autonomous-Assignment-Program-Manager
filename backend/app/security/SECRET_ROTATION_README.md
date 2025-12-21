***REMOVED*** Secret Rotation Service

Automated secret rotation service for the Residency Scheduler backend.

***REMOVED******REMOVED*** Overview

The Secret Rotation Service provides automated, scheduled rotation of sensitive credentials with:

- **Zero-downtime rotation** using grace periods
- **Automatic rollback** on failure
- **Comprehensive audit logging** for compliance
- **Notification system** for rotation events
- **Support for multiple secret types**

***REMOVED******REMOVED*** Supported Secret Types

| Secret Type | Auto-Rotate | Grace Period | Rotation Interval |
|-------------|-------------|--------------|-------------------|
| JWT Signing Key | ✅ | 24 hours | 90 days |
| API Keys | ✅ | 48 hours | 90 days |
| Webhook Secret | ✅ | 72 hours | 180 days |
| Redis Password | ✅ | 1 hour | 90 days |
| S3 Access Key | ✅ | 24 hours | 90 days |
| S3 Secret Key | ✅ | 24 hours | 90 days |
| Database Password | ❌ | None | 180 days |
| Encryption Key | ❌ | None | 365 days |

**Note**: Secrets marked with ❌ for auto-rotate require manual intervention due to their critical nature.

***REMOVED******REMOVED*** Architecture

***REMOVED******REMOVED******REMOVED*** Components

1. **SecretRotationService** (`secret_rotation.py`)
   - Core service for rotating secrets
   - Handles grace periods and rollbacks
   - Manages audit logging

2. **Rotation Tasks** (`rotation_tasks.py`)
   - Celery background tasks
   - Scheduled rotation checks
   - Grace period completion
   - Health monitoring

3. **SecretRotationHistory** (Database Model)
   - Audit trail for all rotations
   - Stores metadata (not actual secrets)
   - Tracks status and timing

***REMOVED******REMOVED******REMOVED*** Rotation Flow

```
1. Check rotation due
   ↓
2. Generate new secret
   ↓
3. Create audit record (IN_PROGRESS)
   ↓
4. Perform rotation
   ↓
5. Enter grace period (if configured)
   ├── Both old and new secrets active
   └── New tokens use new secret
   ↓
6. Complete grace period
   ├── Deactivate old secret
   └── Mark as COMPLETED
```

***REMOVED******REMOVED******REMOVED*** Rollback Flow

```
Rotation fails
   ↓
Create audit record (FAILED)
   ↓
Attempt rollback
   ├── SUCCESS → Mark as ROLLED_BACK
   └── FAILURE → CRITICAL ALERT
```

***REMOVED******REMOVED*** Usage

***REMOVED******REMOVED******REMOVED*** Manual Rotation

```python
from app.security.secret_rotation import rotate_jwt_key
from sqlalchemy.orm import Session

***REMOVED*** Rotate JWT signing key
result = await rotate_jwt_key(
    db=db_session,
    initiated_by=user_id,  ***REMOVED*** Optional
    force=False,           ***REMOVED*** Force even if not due
)

if result.success:
    print(f"Rotation successful. Grace period ends: {result.grace_period_ends}")
else:
    print(f"Rotation failed: {result.error_message}")
```

***REMOVED******REMOVED******REMOVED*** Batch Rotation

```python
from app.security.secret_rotation import rotate_api_keys

***REMOVED*** Rotate all API keys
results = await rotate_api_keys(db=db_session, initiated_by=user_id)

for result in results:
    print(f"{result.secret_type}: {result.success}")
```

***REMOVED******REMOVED******REMOVED*** Check Rotation Status

```python
from app.security.secret_rotation import check_rotation_status

status = await check_rotation_status(db=db_session)

for secret_type, info in status.items():
    if info["due"]:
        print(f"{secret_type} needs rotation!")
        print(f"  Last rotated: {info.get('last_rotated', 'Never')}")
        print(f"  Days overdue: {abs(info.get('days_until_due', 0))}")
```

***REMOVED******REMOVED******REMOVED*** Emergency Rotation

In case of security breach, trigger emergency rotation of all secrets:

```python
from app.security.rotation_tasks import emergency_rotate_all

***REMOVED*** This is a Celery task
emergency_rotate_all.delay(
    reason="Security breach detected",
    initiated_by=str(admin_user_id),
)
```

**⚠️ WARNING**: Emergency rotation should only be used in critical situations.

***REMOVED******REMOVED*** Scheduled Tasks

The following Celery tasks run automatically:

***REMOVED******REMOVED******REMOVED*** Daily (1 AM UTC)
```python
check_scheduled_rotations()
```
- Checks which secrets need rotation
- Triggers automatic rotation for eligible secrets
- Sends reminder notifications for approaching deadlines

***REMOVED******REMOVED******REMOVED*** Hourly (30 minutes past)
```python
complete_grace_periods()
```
- Completes expired grace periods
- Deactivates old secrets
- Updates rotation status to COMPLETED

***REMOVED******REMOVED******REMOVED*** Daily (8 AM UTC)
```python
monitor_rotation_health()
```
- Monitors overall rotation health
- Checks for failed rotations
- Alerts on overdue rotations
- Reports grace period status

***REMOVED******REMOVED******REMOVED*** Monthly (1st at 2 AM UTC)
```python
cleanup_old_rotation_history()
```
- Removes rotation history older than 2 years
- Maintains database performance

***REMOVED******REMOVED*** Grace Period Behavior

***REMOVED******REMOVED******REMOVED*** What is a Grace Period?

During a grace period, **both the old and new secrets are valid**. This ensures zero-downtime rotation.

***REMOVED******REMOVED******REMOVED*** Example: JWT Key Rotation

1. **T+0**: New JWT key generated
   - New tokens signed with new key
   - Old tokens verified with old OR new key

2. **T+24h**: Grace period ends
   - Old key deactivated
   - Only new key accepted

***REMOVED******REMOVED******REMOVED*** Why Grace Periods?

- **Zero downtime**: Existing sessions remain valid
- **Gradual rollover**: Clients have time to refresh tokens
- **Safe deployment**: No service interruption

***REMOVED******REMOVED*** Audit Logging

All rotations are logged to the `secret_rotation_history` table:

```sql
SELECT
    secret_type,
    status,
    rotation_reason,
    started_at,
    completed_at,
    grace_period_ends
FROM secret_rotation_history
WHERE secret_type = 'jwt_signing_key'
ORDER BY started_at DESC
LIMIT 10;
```

***REMOVED******REMOVED******REMOVED*** Audit Fields

- `old_secret_hash`: SHA-256 hash of old secret (NOT the actual secret)
- `new_secret_hash`: SHA-256 hash of new secret (NOT the actual secret)
- `rotation_reason`: Why the rotation occurred
- `initiated_by`: User ID or NULL for automated
- `error_message`: Error details if rotation failed
- `rolled_back`: Whether rollback was performed

***REMOVED******REMOVED*** Security Considerations

***REMOVED******REMOVED******REMOVED*** Secret Storage

**⚠️ CRITICAL**: Actual secret values are NEVER stored in the database.

Only SHA-256 hashes are stored for verification purposes.

***REMOVED******REMOVED******REMOVED*** Who Can Rotate Secrets?

- **Automated rotations**: Triggered by Celery scheduler
- **Manual rotations**: Require admin privileges
- **Emergency rotations**: Require admin or coordinator privileges

***REMOVED******REMOVED******REMOVED*** Notifications

Rotation events trigger notifications at different priority levels:

| Event | Priority | Recipients |
|-------|----------|-----------|
| Scheduled rotation successful | MEDIUM | Admins |
| Rotation failed | HIGH | Admins + Security team |
| Rotation + rollback failed | CRITICAL | All admins (immediate) |
| Grace period completed | LOW | Admins |
| Rotation reminder (7 days) | MEDIUM | Admins |
| Rotation reminder (3 days) | HIGH | Admins |

***REMOVED******REMOVED*** Configuration

Rotation configurations are defined in `SecretRotationService.DEFAULT_CONFIGS`:

```python
RotationConfig(
    secret_type=SecretType.JWT_SIGNING_KEY,
    rotation_interval_days=90,        ***REMOVED*** Rotate every 90 days
    grace_period_hours=24,            ***REMOVED*** 24-hour grace period
    auto_rotate=True,                 ***REMOVED*** Enable automatic rotation
    notify_before_hours=72,           ***REMOVED*** Remind 72 hours before
    max_retries=3,                    ***REMOVED*** Retry up to 3 times
    rollback_on_failure=True,         ***REMOVED*** Auto-rollback on failure
)
```

***REMOVED******REMOVED*** Monitoring

***REMOVED******REMOVED******REMOVED*** Prometheus Metrics

(Future implementation)

```
secret_rotation_total{secret_type, status}
secret_rotation_duration_seconds{secret_type}
secret_grace_period_active{secret_type}
secret_rotation_failures_total{secret_type}
```

***REMOVED******REMOVED******REMOVED*** Health Check Endpoint

```bash
GET /api/security/rotation-health

{
  "health_status": "healthy",
  "failed_rotations_24h": 0,
  "active_grace_periods": 2,
  "overdue_rotations": []
}
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Rotation Failed

1. Check the `secret_rotation_history` table for error details
2. Review application logs for stack traces
3. Verify system health (database, Redis, etc.)
4. If rollback succeeded, system is safe
5. If rollback failed, **IMMEDIATE ACTION REQUIRED**

***REMOVED******REMOVED******REMOVED*** Grace Period Not Completing

1. Check if `complete_grace_periods` task is running
2. Verify Celery worker and beat are operational
3. Manually trigger grace period completion:
   ```python
   service.complete_grace_period(SecretType.JWT_SIGNING_KEY)
   ```

***REMOVED******REMOVED******REMOVED*** Secret Type Not Auto-Rotating

1. Verify `auto_rotate=True` in configuration
2. Check if rotation is actually due
3. Review task logs for errors
4. Manually trigger rotation:
   ```python
   rotate_secret.delay(secret_type="jwt_signing_key", force=True)
   ```

***REMOVED******REMOVED*** Testing

***REMOVED******REMOVED******REMOVED*** Unit Tests

```bash
pytest backend/tests/security/test_secret_rotation.py
```

***REMOVED******REMOVED******REMOVED*** Integration Tests

```bash
pytest backend/tests/security/test_rotation_integration.py
```

***REMOVED******REMOVED******REMOVED*** Manual Testing

```python
***REMOVED*** In Python shell
from app.core.database import SessionLocal
from app.security.secret_rotation import SecretRotationService, SecretType

db = SessionLocal()
service = SecretRotationService(db)

***REMOVED*** Check rotation status
import asyncio
status = asyncio.run(service.check_rotation_due())
print(status)

***REMOVED*** Test rotation
result = asyncio.run(service.rotate_secret(
    SecretType.JWT_SIGNING_KEY,
    reason="Manual test",
    force=True,
))
print(result)
```

***REMOVED******REMOVED*** Migration

To enable secret rotation in an existing deployment:

1. **Add database table**:
   ```bash
   alembic revision --autogenerate -m "Add secret_rotation_history table"
   alembic upgrade head
   ```

2. **Update Celery configuration**:
   - Already configured in `celery_app.py`
   - Restart Celery worker and beat

3. **Configure notifications** (optional):
   - Set up notification recipients
   - Configure webhook endpoints

4. **Perform initial rotation**:
   ```python
   ***REMOVED*** Rotate all secrets to establish baseline
   for secret_type in SecretType:
       if service.DEFAULT_CONFIGS[secret_type].auto_rotate:
           await service.rotate_secret(secret_type, force=True)
   ```

***REMOVED******REMOVED*** Best Practices

1. **Never disable rollback** except for testing
2. **Monitor grace periods** - they should complete on schedule
3. **Set up notifications** - critical for security incidents
4. **Review audit logs** regularly
5. **Test rotation** in staging before production
6. **Keep grace periods reasonable** - too short = outages, too long = security risk
7. **Document manual rotations** - include reason and authorization

***REMOVED******REMOVED*** Future Enhancements

- [ ] HashiCorp Vault integration
- [ ] AWS Secrets Manager integration
- [ ] Automatic secret distribution to distributed systems
- [ ] Slack/PagerDuty integration for alerts
- [ ] Prometheus metrics export
- [ ] Rotation scheduling customization via API
- [ ] Multi-region rotation coordination
- [ ] Blue/green deployment integration

***REMOVED******REMOVED*** Support

For issues or questions:
- Review logs in `backend/logs/`
- Check Celery task status
- Consult audit logs in database
- Contact security team for critical failures

---

**Last Updated**: 2025-12-20
**Version**: 1.0.0
**Maintainer**: Security Team
