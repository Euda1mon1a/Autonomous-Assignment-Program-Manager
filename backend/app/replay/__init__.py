"""Request replay service for testing and debugging.

This module provides functionality for:
- Capturing HTTP requests and responses
- Replaying captured requests with timing control
- Modifying requests before replay
- Comparing responses
- Bulk replay operations
- Scheduling replay tasks

Usage:
    from app.replay.service import ReplayService

    # Capture a request
    service = ReplayService(db)
    await service.capture_request(
        method="POST",
        url="/api/schedule/generate",
        headers={"Content-Type": "application/json"},
        body={"start_date": "2025-01-01"},
        response_status=200,
        response_body={"schedule_id": "123"},
    )

    # Replay a request
    result = await service.replay_request(request_id)

    # Bulk replay with filters
    results = await service.bulk_replay(
        filters={"status_code": 200, "created_after": "2025-01-01"}
    )
"""

from app.replay.service import ReplayService

__all__ = ["ReplayService"]
