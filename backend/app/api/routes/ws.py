"""WebSocket API routes for real-time updates."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import HTTPException

from app.core.security import get_current_active_user, get_current_user, verify_token
from app.db.session import get_db
from app.models.user import User
from app.websocket.manager import get_connection_manager

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_websocket_user(
    websocket: WebSocket, token: str | None = Query(None), db=Depends(get_db)
) -> User | None:
    """
    Authenticate WebSocket connection via token query parameter or cookie.

    Supports two authentication methods:
    1. Token in query parameter: ws://server/api/v1/ws?token=<JWT>
    2. Token in httpOnly cookie: access_token cookie (fallback)

    Args:
        websocket: WebSocket connection
        token: JWT token from query string
        db: Database session

    Returns:
        User if authenticated, None otherwise
    """
    # Try query parameter first
    if not token:
        # Fallback: try to extract from cookies header
        cookies_header = websocket.headers.get("cookie", "")
        for cookie in cookies_header.split(";"):
            cookie = cookie.strip()
            if cookie.startswith("access_token="):
                token = cookie.split("=", 1)[1]
                logger.debug("WebSocket auth: token extracted from cookie")
                break

    if not token:
        logger.warning(
            "WebSocket connection attempt without token (no query param or cookie)"
        )
        return None

    token_data = verify_token(token, db)
    if token_data is None or token_data.user_id is None:
        logger.warning("WebSocket connection with invalid token")
        return None

    from app.core.security import get_user_by_id

    user = get_user_by_id(db, UUID(token_data.user_id))
    if user is None or not user.is_active:
        logger.warning(f"WebSocket connection for inactive user: {token_data.user_id}")
        return None

    return user


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None),
    db=Depends(get_db),
) -> None:
    """
    WebSocket endpoint for real-time schedule updates.

    Query Parameters:
        token: JWT access token for authentication

    Protocol:
        - Client connects with token query parameter
        - Server sends connection_ack event
        - Client can send subscribe/unsubscribe messages
        - Server broadcasts events to subscribed clients
        - Client sends ping for keepalive, server responds with pong

    Message Types (Client -> Server):
        {
            "action": "subscribe_schedule",
            "schedule_id": "uuid"
        }
        {
            "action": "subscribe_person",
            "person_id": "uuid"
        }
        {
            "action": "unsubscribe_schedule",
            "schedule_id": "uuid"
        }
        {
            "action": "unsubscribe_person",
            "person_id": "uuid"
        }
        {
            "action": "ping"
        }

    Event Types (Server -> Client):
        - schedule_updated
        - assignment_changed
        - swap_requested
        - swap_approved
        - conflict_detected
        - resilience_alert
        - connection_ack
        - pong
    """
    # Authenticate user
    user = await get_websocket_user(websocket, token, db)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    manager = get_connection_manager()
    connection = await manager.connect(websocket, user.id)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()

            action = data.get("action")

            if action == "subscribe_schedule":
                schedule_id = data.get("schedule_id")
                if schedule_id:
                    try:
                        schedule_uuid = UUID(schedule_id)
                        await manager.subscribe_to_schedule(user.id, schedule_uuid)
                        logger.info(
                            f"User {user.id} subscribed to schedule {schedule_uuid}"
                        )
                    except ValueError:
                        logger.warning(f"Invalid schedule_id: {schedule_id}")

            elif action == "subscribe_person":
                person_id = data.get("person_id")
                if person_id:
                    try:
                        person_uuid = UUID(person_id)
                        await manager.subscribe_to_person(user.id, person_uuid)
                        logger.info(
                            f"User {user.id} subscribed to person {person_uuid}"
                        )
                    except ValueError:
                        logger.warning(f"Invalid person_id: {person_id}")

            elif action == "unsubscribe_schedule":
                schedule_id = data.get("schedule_id")
                if schedule_id:
                    try:
                        schedule_uuid = UUID(schedule_id)
                        await manager.unsubscribe_from_schedule(user.id, schedule_uuid)
                        logger.info(
                            f"User {user.id} unsubscribed from schedule {schedule_uuid}"
                        )
                    except ValueError:
                        logger.warning(f"Invalid schedule_id: {schedule_id}")

            elif action == "unsubscribe_person":
                person_id = data.get("person_id")
                if person_id:
                    try:
                        person_uuid = UUID(person_id)
                        await manager.unsubscribe_from_person(user.id, person_uuid)
                        logger.info(
                            f"User {user.id} unsubscribed from person {person_uuid}"
                        )
                    except ValueError:
                        logger.warning(f"Invalid person_id: {person_id}")

            elif action == "ping":
                await manager.handle_ping(connection)

            else:
                logger.warning(f"Unknown WebSocket action: {action}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {e}", exc_info=True)
    finally:
        await manager.disconnect(connection)


@router.get("/ws/stats")
async def get_websocket_stats(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str | dict]:
    """
    Get WebSocket connection statistics.

    Requires authentication.

    Returns:
        Dictionary with connection statistics
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    manager = get_connection_manager()
    stats = manager.get_stats()

    return {
        "status": "ok",
        "stats": stats,
    }


@router.get("/ws/health")
async def websocket_health() -> dict[str, str | bool | dict]:
    """
    WebSocket subsystem health check.

    Returns:
        Health status
    """
    manager = get_connection_manager()
    stats = manager.get_stats()

    return {
        "status": "healthy",
        "websocket_enabled": True,
        "connections": stats,
    }
