"""
Event Handlers Package

Event handlers respond to published events and perform side effects:
- Send notifications
- Update projections
- Trigger workflows
- Integrate with external systems

Handlers are organized by domain:
- schedule_events: Schedule-related event handlers
- assignment_events: Assignment-related event handlers
- compliance_events: ACGME compliance event handlers

Usage:
    from app.events.handlers import register_all_handlers

    # Register all handlers with event bus
    register_all_handlers(event_bus, db)
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.events.event_bus import EventBus

logger = logging.getLogger(__name__)


def register_all_handlers(event_bus: EventBus, db: Session):
    """
    Register all event handlers with the event bus.

    Args:
        event_bus: EventBus instance
        db: Database session for handlers that need persistence
    """
    from app.events.handlers.schedule_events import register_schedule_handlers

    logger.info("Registering all event handlers...")

    # Register domain-specific handlers
    register_schedule_handlers(event_bus, db)

    logger.info("All event handlers registered successfully")


__all__ = [
    "register_all_handlers",
]
