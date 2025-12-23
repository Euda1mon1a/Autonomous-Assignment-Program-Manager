"""Transactional Outbox Pattern Implementation.

This module implements the transactional outbox pattern for reliable
event publishing in distributed systems.

Overview:
---------
The transactional outbox pattern solves the dual-write problem:
- Business data changes are written to the database
- Events/messages are written to the same database transaction
- A separate relay process publishes messages from the database to the message broker

This ensures exactly-once delivery semantics and prevents:
- Business transaction succeeds but message fails to publish
- Message publishes but business transaction fails

Components:
----------
1. OutboxMessage: Database model for storing messages
2. OutboxWriter: Writes messages within database transactions
3. OutboxRelay: Publishes messages from database to message broker
4. OutboxCleaner: Archives and cleans up old messages
5. Celery Tasks: Background tasks for relay, archival, and cleanup
6. Metrics: Monitoring and alerting

Usage Example:
-------------
***REMOVED*** In a service/route that creates an assignment:

from app.outbox import OutboxWriter

def create_assignment(db: Session, data: dict):
    ***REMOVED*** Write business data
    assignment = Assignment(**data)
    db.add(assignment)

    ***REMOVED*** Write outbox message in SAME transaction
    writer = OutboxWriter(db)
    writer.write_message(
        aggregate_type="assignment",
        aggregate_id=assignment.id,
        event_type="assignment.created",
        payload={
            "assignment_id": str(assignment.id),
            "person_id": str(assignment.person_id),
            "date": str(assignment.date),
        }
    )

    ***REMOVED*** Commit both atomically
    db.commit()

    ***REMOVED*** Message will be published by background relay task


Configuration:
-------------
Add to celery_app.py beat_schedule:

    "outbox-relay": {
        "task": "app.outbox.tasks.relay_outbox_messages",
        "schedule": crontab(minute="*/1"),  ***REMOVED*** Every minute
        "options": {"queue": "outbox"},
    },
    "outbox-archive": {
        "task": "app.outbox.tasks.archive_published_messages",
        "schedule": crontab(hour="*/6"),  ***REMOVED*** Every 6 hours
        "options": {"queue": "outbox"},
    },
    "outbox-cleanup-archive": {
        "task": "app.outbox.tasks.cleanup_old_archive",
        "schedule": crontab(hour=3, minute=0),  ***REMOVED*** Daily at 3 AM
        "options": {"queue": "outbox"},
    },
    "outbox-cleanup-failed": {
        "task": "app.outbox.tasks.cleanup_failed_messages",
        "schedule": crontab(hour=4, minute=0),  ***REMOVED*** Daily at 4 AM
        "options": {"queue": "outbox"},
    },
    "outbox-metrics": {
        "task": "app.outbox.tasks.collect_outbox_metrics",
        "schedule": crontab(minute="*/5"),  ***REMOVED*** Every 5 minutes
        "options": {"queue": "outbox"},
    },


Features:
--------
- Exactly-once delivery guarantees
- Message ordering preservation per aggregate
- Automatic retry with exponential backoff
- Dead letter queue for failed messages
- Archival and cleanup of old messages
- Comprehensive metrics and monitoring
- Health checks and anomaly detection

References:
----------
- https://microservices.io/patterns/data/transactional-outbox.html
- Enterprise Integration Patterns (Hohpe & Woolf)
- Designing Data-Intensive Applications (Kleppmann)
"""

***REMOVED*** Models
***REMOVED*** Metrics and monitoring
from app.outbox.metrics import (
    OutboxMetricsCollector,
    OutboxMonitor,
)
from app.outbox.models import (
    OutboxArchive,
    OutboxMessage,
    OutboxStatus,
)

***REMOVED*** Core services
from app.outbox.outbox import (
    OutboxCleaner,
    OutboxRelay,
    OutboxWriter,
)

***REMOVED*** Tasks are imported separately to avoid circular imports
***REMOVED*** Use: from app.outbox.tasks import relay_outbox_messages

__all__ = [
    ***REMOVED*** Models
    "OutboxMessage",
    "OutboxArchive",
    "OutboxStatus",
    ***REMOVED*** Services
    "OutboxWriter",
    "OutboxRelay",
    "OutboxCleaner",
    ***REMOVED*** Metrics
    "OutboxMetricsCollector",
    "OutboxMonitor",
]
