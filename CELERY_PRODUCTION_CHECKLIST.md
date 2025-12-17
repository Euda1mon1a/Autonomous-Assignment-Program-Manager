# Celery Production Implementation Checklist

This checklist covers production readiness tasks for the Celery background task system.

## Status: Development-Ready, Production Setup Pending

The Celery configuration is complete and functional for development and testing. The following items are needed for production deployment:

## Critical Items (Required for Production)

### 1. Email Notification Implementation
**Status**: ⚠️ Stubbed (logs only)
**Location**: `/home/user/Autonomous-Assignment-Program-Manager/backend/app/notifications/tasks.py` - `send_email()` task
**Priority**: HIGH

**Current State**:
```python
@shared_task
def send_email(to: str, subject: str, body: str, html: str | None = None):
    logger.info("Sending email to %s: %s", to, subject)
    # NOTE: Implement email sending here
    return {"timestamp": datetime.now().isoformat(), "to": to, "status": "queued"}
```

**Required Implementation**:

Choose one of these options:

#### Option A: SMTP (Self-hosted or Gmail)
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import get_settings

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, to: str, subject: str, body: str, html: str | None = None):
    settings = get_settings()

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_FROM
        msg['To'] = to

        msg.attach(MIMEText(body, 'plain'))
        if html:
            msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to}")
        return {"status": "sent", "to": to, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        raise self.retry(exc=e)
```

**Environment Variables**:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@hospital.org
```

#### Option B: SendGrid
```python
import sendgrid
from sendgrid.helpers.mail import Mail
from app.core.config import get_settings

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, to: str, subject: str, body: str, html: str | None = None):
    settings = get_settings()

    try:
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        message = Mail(
            from_email=settings.SMTP_FROM,
            to_emails=to,
            subject=subject,
            html_content=html or body
        )

        response = sg.send(message)
        logger.info(f"Email sent via SendGrid to {to}: {response.status_code}")
        return {"status": "sent", "to": to, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        raise self.retry(exc=e)
```

**Requirements**: Add to `requirements.txt`:
```
sendgrid>=6.9.0
```

**Environment Variables**:
```bash
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
SMTP_FROM=noreply@hospital.org
```

#### Option C: AWS SES
```python
import boto3
from botocore.exceptions import ClientError
from app.core.config import get_settings

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, to: str, subject: str, body: str, html: str | None = None):
    settings = get_settings()

    try:
        client = boto3.client('ses', region_name=settings.AWS_REGION)

        response = client.send_email(
            Source=settings.SMTP_FROM,
            Destination={'ToAddresses': [to]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body},
                    'Html': {'Data': html or body}
                }
            }
        )

        logger.info(f"Email sent via SES to {to}: {response['MessageId']}")
        return {"status": "sent", "to": to, "timestamp": datetime.now().isoformat()}

    except ClientError as e:
        logger.error(f"Failed to send email to {to}: {e}")
        raise self.retry(exc=e)
```

**Requirements**: Add to `requirements.txt`:
```
boto3>=1.26.0
```

**Environment Variables**:
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
SMTP_FROM=noreply@hospital.org
```

---

### 2. Webhook Notification Implementation
**Status**: ⚠️ Stubbed (logs only)
**Location**: `/home/user/Autonomous-Assignment-Program-Manager/backend/app/notifications/tasks.py` - `send_webhook()` task
**Priority**: MEDIUM

**Current State**:
```python
@shared_task
def send_webhook(url: str, payload: dict):
    logger.info("Sending webhook to %s", url)
    # NOTE: Implement HTTP POST here
    return {"timestamp": datetime.now().isoformat(), "url": url, "status": "queued"}
```

**Required Implementation**:

```python
import httpx
from app.core.config import get_settings

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_webhook(self, url: str, payload: dict):
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

        logger.info(f"Webhook sent successfully to {url}: {response.status_code}")
        return {
            "status": "sent",
            "url": url,
            "status_code": response.status_code,
            "timestamp": datetime.now().isoformat()
        }

    except httpx.HTTPError as e:
        logger.error(f"Failed to send webhook to {url}: {e}")
        raise self.retry(exc=e)
```

**Requirements**: Add to `requirements.txt`:
```
httpx>=0.28.0
```

---

### 3. Alert Recipients Configuration
**Status**: ⚠️ Empty list in config
**Location**: `/home/user/Autonomous-Assignment-Program-Manager/backend/app/core/config.py`
**Priority**: HIGH

**Current State**:
```python
RESILIENCE_ALERT_RECIPIENTS: list[str] = []  # Email addresses for alerts
```

**Required Action**:
Set in production `.env`:
```bash
RESILIENCE_ALERT_RECIPIENTS=["chief-resident@hospital.org", "program-director@hospital.org", "coordinator@hospital.org"]
```

---

## Recommended Items (Enhanced Production Features)

### 4. Flower Monitoring Dashboard
**Status**: ❌ Not installed
**Priority**: HIGH
**Effort**: 5 minutes

**Installation**:
```bash
pip install flower
```

**Add to docker-compose.yml**:
```yaml
flower:
  build: ./backend
  command: celery -A app.core.celery_app flower --port=5555
  ports:
    - "5555:5555"
  environment:
    CELERY_BROKER_URL: redis://redis:6379/0
    CELERY_RESULT_BACKEND: redis://redis:6379/0
  depends_on:
    - redis
  networks:
    - app-network
```

**Access**: http://localhost:5555

**Features**:
- Real-time task monitoring
- Worker status and stats
- Task history and results
- Task execution graphs
- Worker management

---

### 5. Dedicated Queue Workers
**Status**: ✓ Single worker handles all queues
**Priority**: MEDIUM (for high load environments)

**Current State**: One worker processes all three queues (default, resilience, notifications)

**Recommended for Production**:
Run separate workers per queue for better isolation and scaling:

```yaml
# docker-compose.yml
celery-worker-resilience:
  build: ./backend
  command: celery -A app.core.celery_app worker --loglevel=info -Q resilience --concurrency=2
  # ... other config

celery-worker-notifications:
  build: ./backend
  command: celery -A app.core.celery_app worker --loglevel=info -Q notifications --concurrency=8
  # ... other config

celery-worker-default:
  build: ./backend
  command: celery -A app.core.celery_app worker --loglevel=info -Q default --concurrency=4
  # ... other config
```

**Benefits**:
- Independent scaling per workload
- Resource isolation
- Better failure containment
- Prioritization flexibility

---

### 6. Log Aggregation
**Status**: ❌ Local logs only
**Priority**: MEDIUM
**Effort**: 1-2 hours

**Recommended**: Ship Celery logs to centralized logging system

**Options**:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Loki + Grafana**
- **CloudWatch Logs** (AWS)
- **Stackdriver** (GCP)

**Example Loki Configuration**:
```yaml
# docker-compose.yml
celery-worker:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
      labels: "service,component"
  labels:
    - "service=residency-scheduler"
    - "component=celery-worker"
```

---

### 7. Sentry Error Tracking
**Status**: ✓ Sentry SDK installed, needs configuration
**Priority**: MEDIUM
**Effort**: 15 minutes

**Current State**: `sentry-sdk[fastapi]==2.48.0` in requirements.txt

**Configuration Needed**:

In `backend/app/core/celery_app.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[CeleryIntegration()],
    environment=settings.ENVIRONMENT,
    traces_sample_rate=0.1,
)
```

**Environment Variables**:
```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production
```

---

### 8. Prometheus Alerts
**Status**: ✓ Metrics exposed, alerts not configured
**Priority**: MEDIUM
**Effort**: 30 minutes

**Current State**: Resilience tasks update Prometheus metrics via `app.resilience.metrics`

**Required**: Configure Prometheus AlertManager rules

**Example Alert Rules** (`prometheus-alerts.yml`):
```yaml
groups:
  - name: celery
    interval: 30s
    rules:
      - alert: CeleryWorkerDown
        expr: up{job="celery-worker"} == 0
        for: 2m
        annotations:
          summary: "Celery worker is down"

      - alert: CeleryHighQueueSize
        expr: celery_queue_length > 100
        for: 5m
        annotations:
          summary: "Celery queue has {{ $value }} tasks"

      - alert: CeleryHighFailureRate
        expr: rate(celery_task_failed_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Celery task failure rate is {{ $value }}"

      - alert: ResilienceDefenseLevelCritical
        expr: resilience_defense_level >= 3
        for: 1m
        annotations:
          summary: "Resilience defense level is CRITICAL"

      - alert: ResilienceUtilizationHigh
        expr: resilience_utilization_rate > 0.85
        for: 10m
        annotations:
          summary: "Utilization at {{ $value }}%"
```

---

### 9. Beat Schedule Persistence
**Status**: ✓ Redis backend (ephemeral)
**Priority**: LOW
**Effort**: 10 minutes

**Current State**: Beat schedule in memory/Redis

**Recommended for Production**: Use database backend for schedule persistence

**Configuration**:
```python
# backend/app/core/celery_app.py
celery_app.conf.update(
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
    # Or use sqlalchemy-celery-beat for SQLAlchemy
)
```

**Benefits**:
- Dynamic schedule updates
- Schedule persistence across restarts
- Web UI for schedule management

---

### 10. Task Result Storage
**Status**: ✓ Redis (1 hour expiration)
**Priority**: LOW
**Consideration**: Current setup is fine for most cases

**Current State**: Task results stored in Redis, expire after 1 hour

**Alternative for Long-term Storage**:
```python
# Store important task results in database
celery_app.conf.update(
    result_backend='db+postgresql://...',
    result_extended=True,
)
```

---

## Security Checklist

### 11. Redis Security
**Status**: ⚠️ Basic setup, needs hardening
**Priority**: HIGH

**Required Actions**:
1. **Enable Redis password**:
   ```bash
   # redis.conf
   requirepass your-strong-password-here
   ```

   Update `.env`:
   ```bash
   REDIS_URL=redis://:your-strong-password-here@redis:6379/0
   ```

2. **Bind to localhost only** (if not using Docker network):
   ```bash
   # redis.conf
   bind 127.0.0.1
   ```

3. **Disable dangerous commands**:
   ```bash
   # redis.conf
   rename-command FLUSHDB ""
   rename-command FLUSHALL ""
   rename-command CONFIG ""
   ```

4. **Enable TLS** (for production):
   ```bash
   # redis.conf
   tls-port 6380
   tls-cert-file /path/to/redis.crt
   tls-key-file /path/to/redis.key
   tls-ca-cert-file /path/to/ca.crt
   ```

---

### 12. Task Serialization Security
**Status**: ✓ JSON only (secure)
**Priority**: ✅ COMPLETE

**Current State**: Tasks use JSON serialization only
```python
task_serializer="json",
accept_content=["json"],
```

**Note**: This is the secure configuration. Do NOT enable pickle serialization.

---

## Performance Optimization

### 13. Connection Pooling
**Status**: ✓ Configured
**Priority**: ✅ COMPLETE

**Current Settings**:
```python
worker_prefetch_multiplier=1,
worker_concurrency=4,
```

**Tuning Recommendations**:
- **High I/O tasks** (notifications): Increase concurrency (8-16)
- **CPU-bound tasks** (analysis): Match CPU cores
- **Memory-intensive tasks**: Reduce concurrency (1-2)

---

### 14. Task Time Limits
**Status**: ✓ Configured
**Priority**: ✅ COMPLETE

**Current Settings**:
```python
task_time_limit=600,  # 10 minutes
task_soft_time_limit=540,  # 9 minutes
```

**Recommendation**: Monitor task execution times and adjust if needed.

---

### 15. Result Expiration
**Status**: ✓ Configured (1 hour)
**Priority**: ✅ COMPLETE

**Current Setting**:
```python
result_expires=3600,  # 1 hour
```

**Recommendation**: Reduce if results not needed, increase if results accessed later.

---

## Testing Checklist

### 16. Integration Tests
**Status**: ⚠️ Manual testing only
**Priority**: MEDIUM

**Recommended**: Add automated integration tests

**Example Test** (`backend/tests/integration/test_celery_tasks.py`):
```python
import pytest
from app.resilience.tasks import periodic_health_check
from app.notifications.tasks import send_email

def test_periodic_health_check(db_session):
    """Test health check task executes successfully."""
    result = periodic_health_check.apply().get()
    assert result["status"] in ["healthy", "warning", "critical"]

def test_send_email_task():
    """Test email task queues successfully."""
    result = send_email.apply_async(
        kwargs={
            "to": "test@example.com",
            "subject": "Test",
            "body": "Test message"
        }
    )
    assert result.status in ["PENDING", "SUCCESS"]
```

---

## Deployment Checklist

### Pre-deployment
- [ ] Email integration implemented and tested
- [ ] Webhook integration implemented and tested
- [ ] Alert recipients configured
- [ ] Redis password enabled
- [ ] Sentry DSN configured
- [ ] Environment variables set in production `.env`
- [ ] Flower dashboard deployed
- [ ] Prometheus alerts configured
- [ ] Log aggregation configured

### During Deployment
- [ ] Run `python verify_celery.py` to verify configuration
- [ ] Start Redis service
- [ ] Start Celery worker
- [ ] Start Celery beat
- [ ] Verify workers are registered: `celery -A app.core.celery_app inspect active`
- [ ] Verify beat schedule: `celery -A app.core.celery_app inspect scheduled`
- [ ] Run health check: `./scripts/health-check.sh --docker`

### Post-deployment
- [ ] Monitor worker logs for errors
- [ ] Verify periodic tasks execute on schedule
- [ ] Test email notifications
- [ ] Test alert triggering
- [ ] Monitor Prometheus metrics
- [ ] Set up alerts for worker failures

---

## Summary

**Current Status**: Development-ready with production infrastructure in place

**Critical Path to Production**:
1. Implement email sending (Option A, B, or C) - 1 hour
2. Implement webhook sending - 30 minutes
3. Configure alert recipients - 5 minutes
4. Enable Redis password - 10 minutes
5. Deploy Flower dashboard - 15 minutes
6. Configure Prometheus alerts - 30 minutes

**Total Time to Production**: ~3 hours

**Files to Modify**:
1. `/home/user/Autonomous-Assignment-Program-Manager/backend/app/notifications/tasks.py` - Implement email/webhook
2. `/home/user/Autonomous-Assignment-Program-Manager/backend/.env` - Add configuration
3. `/home/user/Autonomous-Assignment-Program-Manager/docker-compose.yml` - Add Flower (optional)
4. Redis configuration - Enable password

**Configuration is COMPLETE** for development and testing. The above items are needed for production deployment.
