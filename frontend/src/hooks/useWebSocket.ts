/**
 * WebSocket Client Hook for Real-time Updates
 *
 * Provides a React hook for connecting to the backend WebSocket endpoint
 * with automatic reconnection, JWT authentication, and typed event handling.
 *
 * Features:
 * - Auto-reconnect with exponential backoff
 * - JWT authentication via query parameter
 * - Connection state management
 * - Message parsing and type safety
 * - Ping/pong keepalive
 * - Subscription management for schedules and persons
 *
 * @module hooks/useWebSocket
 */
import { useCallback, useEffect, useRef, useState } from 'react'

// ============================================================================
// Types
// ============================================================================

/**
 * Event types supported by the WebSocket server.
 * Matches backend EventType enum from websocket/events.py
 */
export type EventType =
  | 'schedule_updated'
  | 'assignment_changed'
  | 'swap_requested'
  | 'swap_approved'
  | 'conflict_detected'
  | 'resilience_alert'
  | 'connection_ack'
  | 'ping'
  | 'pong'

/**
 * Base WebSocket event structure.
 * All events from the server follow this format.
 */
export interface WebSocketEvent<T = unknown> {
  /** Type of the event */
  eventType: EventType
  /** ISO 8601 timestamp when event was created */
  timestamp: string
  /** Event-specific payload data */
  data?: T
  /** Additional event properties */
  [key: string]: unknown
}

/**
 * Schedule updated event payload.
 */
export interface ScheduleUpdatedEvent extends WebSocketEvent {
  eventType: 'schedule_updated'
  scheduleId: string | null
  academicYear_id: string | null
  userId: string | null
  update_type: 'generated' | 'modified' | 'regenerated'
  affected_blocks_count: number
  message: string
}

/**
 * Assignment changed event payload.
 */
export interface AssignmentChangedEvent extends WebSocketEvent {
  eventType: 'assignment_changed'
  assignmentId: string
  personId: string
  blockId: string
  rotationTemplateId: string | null
  change_type: 'created' | 'updated' | 'deleted'
  changed_by: string | null
  message: string
}

/**
 * Swap requested event payload.
 */
export interface SwapRequestedEvent extends WebSocketEvent {
  eventType: 'swap_requested'
  swapId: string
  requester_id: string
  target_personId: string | null
  swapType: 'oneToOne' | 'absorb'
  affected_assignments: string[]
  message: string
}

/**
 * Swap approved event payload.
 */
export interface SwapApprovedEvent extends WebSocketEvent {
  eventType: 'swap_approved'
  swapId: string
  requester_id: string
  target_personId: string | null
  approved_by: string
  affected_assignments: string[]
  message: string
}

/**
 * Conflict detected event payload.
 */
export interface ConflictDetectedEvent extends WebSocketEvent {
  eventType: 'conflict_detected'
  conflictId: string | null
  personId: string
  conflict_type: 'double_booking' | 'acgmeViolation' | 'absence_overlap'
  severity: 'low' | 'medium' | 'high' | 'critical'
  affected_blocks: string[]
  message: string
}

/**
 * Resilience alert event payload.
 */
export interface ResilienceAlertEvent extends WebSocketEvent {
  eventType: 'resilience_alert'
  alert_type: 'utilization_high' | 'n1_failure' | 'n2_failure' | 'defenseLevel_change'
  severity: 'green' | 'yellow' | 'orange' | 'red' | 'black'
  current_utilization: number | null
  defenseLevel: string | null
  affected_persons: string[]
  message: string
  recommendations: string[]
}

/**
 * Connection acknowledgment event payload.
 */
export interface ConnectionAckEvent extends WebSocketEvent {
  eventType: 'connection_ack'
  userId: string
  message: string
}

/**
 * Union type of all possible WebSocket events.
 */
export type AnyWebSocketEvent =
  | ScheduleUpdatedEvent
  | AssignmentChangedEvent
  | SwapRequestedEvent
  | SwapApprovedEvent
  | ConflictDetectedEvent
  | ResilienceAlertEvent
  | ConnectionAckEvent
  | WebSocketEvent<unknown>

/**
 * Client-to-server message types.
 */
export type ClientAction =
  | 'subscribe_schedule'
  | 'unsubscribe_schedule'
  | 'subscribe_person'
  | 'unsubscribe_person'
  | 'ping'

/**
 * Client message structure.
 */
export interface ClientMessage {
  action: ClientAction
  scheduleId?: string
  personId?: string
}

/**
 * Connection state enum.
 */
export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting'

/**
 * Options for the useWebSocket hook.
 */
export interface UseWebSocketOptions {
  /**
   * WebSocket URL. Defaults to ws://localhost:8000/api/v1/ws
   * Will be automatically constructed from NEXT_PUBLIC_API_URL if not provided.
   */
  url?: string

  /**
   * JWT access token for authentication.
   * If not provided, the hook will try to get it from the auth module.
   */
  token?: string

  /**
   * Callback when a message is received from the server.
   */
  onMessage?: (event: AnyWebSocketEvent) => void

  /**
   * Callback when connection is established.
   */
  onConnect?: () => void

  /**
   * Callback when connection is closed.
   */
  onDisconnect?: (event: CloseEvent) => void

  /**
   * Callback when an error occurs.
   */
  onError?: (error: Event) => void

  /**
   * Whether to automatically reconnect on disconnect.
   * Default: true
   */
  reconnect?: boolean

  /**
   * Initial reconnection interval in milliseconds.
   * Default: 1000 (1 second)
   */
  reconnectInterval?: number

  /**
   * Maximum reconnection interval in milliseconds.
   * Default: 30000 (30 seconds)
   */
  maxReconnectInterval?: number

  /**
   * Maximum number of reconnection attempts.
   * Default: 10
   */
  reconnectAttempts?: number

  /**
   * Ping interval in milliseconds for keepalive.
   * Default: 30000 (30 seconds)
   */
  pingInterval?: number

  /**
   * Whether to connect automatically when the hook mounts.
   * Default: true
   */
  autoConnect?: boolean
}

/**
 * Return type of the useWebSocket hook.
 */
export interface UseWebSocketReturn {
  /** Current connection state */
  connectionState: ConnectionState

  /** Whether the WebSocket is currently connected */
  isConnected: boolean

  /** The last message received from the server */
  lastMessage: AnyWebSocketEvent | null

  /** Number of reconnection attempts made */
  reconnectAttempts: number

  /**
   * Send a message to the server.
   * @param message - The message to send
   */
  send: (message: ClientMessage) => void

  /**
   * Manually connect to the WebSocket server.
   */
  connect: () => void

  /**
   * Manually disconnect from the WebSocket server.
   */
  disconnect: () => void

  /**
   * Subscribe to schedule updates.
   * @param scheduleId - The schedule ID to subscribe to
   */
  subscribeToSchedule: (scheduleId: string) => void

  /**
   * Unsubscribe from schedule updates.
   * @param scheduleId - The schedule ID to unsubscribe from
   */
  unsubscribeFromSchedule: (scheduleId: string) => void

  /**
   * Subscribe to person updates.
   * @param personId - The person ID to subscribe to
   */
  subscribeToPerson: (personId: string) => void

  /**
   * Unsubscribe from person updates.
   * @param personId - The person ID to unsubscribe from
   */
  unsubscribeFromPerson: (personId: string) => void
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Constructs the WebSocket URL from the API base URL.
 *
 * @param apiUrl - The HTTP API base URL
 * @returns The WebSocket URL
 */
function getWebSocketUrl(apiUrl?: string): string {
  // Use provided URL or get from environment
  const baseUrl = apiUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

  // Convert http(s) to ws(s)
  const wsUrl = baseUrl.replace(/^http/, 'ws')

  // Ensure the URL ends with /ws
  if (wsUrl.endsWith('/')) {
    return `${wsUrl}ws`
  }
  return `${wsUrl}/ws`
}

/**
 * Parses a WebSocket message into a typed event.
 *
 * @param data - The raw message data
 * @returns Parsed event or null if parsing fails
 */
function parseMessage(data: string): AnyWebSocketEvent | null {
  try {
    const parsed = JSON.parse(data) as AnyWebSocketEvent
    if (!parsed.eventType) {
      // Invalid message format
      return null
    }
    return parsed
  } catch (error) {
    // Failed to parse WebSocket message
    return null
  }
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * React hook for WebSocket connection management.
 *
 * Provides a WebSocket connection to the backend with automatic reconnection,
 * authentication, and typed event handling.
 *
 * @param options - Configuration options for the WebSocket connection
 * @returns WebSocket state and control functions
 *
 * @example
 * ```tsx
 * function ScheduleView() {
 *   const {
 *     isConnected,
 *     lastMessage,
 *     subscribeToSchedule,
 *     unsubscribeFromSchedule
 *   } = useWebSocket({
 *     onMessage: (event) => {
 *       if (event.eventType === 'schedule_updated') {
 *         console.log('Schedule updated:', event.message);
 *         // Refetch schedule data
 *       }
 *     },
 *     onConnect: () => {
 *       console.log('WebSocket connected');
 *     }
 *   });
 *
 *   useEffect(() => {
 *     if (isConnected && scheduleId) {
 *       subscribeToSchedule(scheduleId);
 *       return () => unsubscribeFromSchedule(scheduleId);
 *     }
 *   }, [isConnected, scheduleId]);
 *
 *   return (
 *     <div>
 *       <ConnectionIndicator connected={isConnected} />
 *       <ScheduleGrid />
 *     </div>
 *   );
 * }
 * ```
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url,
    token,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnect = true,
    reconnectInterval = 1000,
    maxReconnectInterval = 30000,
    reconnectAttempts: reconnectAttempts = 10,
    pingInterval = 30000,
    autoConnect = true,
  } = options

  // State
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [lastMessage, setLastMessage] = useState<AnyWebSocketEvent | null>(null)
  const [reconnectAttemptsCount, setReconnectAttemptsCount] = useState(0)

  // Refs for stable references
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const currentReconnectInterval = useRef(reconnectInterval)
  const mountedRef = useRef(true)
  const manualDisconnectRef = useRef(false)

  // Store callbacks in refs to avoid re-renders
  const onMessageRef = useRef(onMessage)
  const onConnectRef = useRef(onConnect)
  const onDisconnectRef = useRef(onDisconnect)
  const onErrorRef = useRef(onError)

  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage
    onConnectRef.current = onConnect
    onDisconnectRef.current = onDisconnect
    onErrorRef.current = onError
  }, [onMessage, onConnect, onDisconnect, onError])

  /**
   * Clears all timers and intervals.
   */
  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
  }, [])

  /**
   * Sends a ping message to keep the connection alive.
   */
  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'ping' }))
    }
  }, [])

  /**
   * Starts the ping interval for keepalive.
   */
  const startPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
    }
    pingIntervalRef.current = setInterval(sendPing, pingInterval)
  }, [pingInterval, sendPing])

  /**
   * Disconnects the WebSocket connection.
   */
  const disconnect = useCallback(() => {
    manualDisconnectRef.current = true
    clearTimers()

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect')
      wsRef.current = null
    }

    setConnectionState('disconnected')
    setReconnectAttemptsCount(0)
    currentReconnectInterval.current = reconnectInterval
  }, [clearTimers, reconnectInterval])

  /**
   * Connects to the WebSocket server.
   */
  const connect = useCallback(() => {
    // Don't connect if we're already connected or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN ||
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      return
    }

    // Clear any existing connection
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    manualDisconnectRef.current = false
    clearTimers()

    // Construct the WebSocket URL with token
    const wsUrl = getWebSocketUrl(url)
    const authToken = token || ''

    // Add token as query parameter
    const urlWithToken = authToken ? `${wsUrl}?token=${encodeURIComponent(authToken)}` : wsUrl

    setConnectionState('connecting')

    try {
      const ws = new WebSocket(urlWithToken)
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) return

        setConnectionState('connected')
        setReconnectAttemptsCount(0)
        currentReconnectInterval.current = reconnectInterval

        // Start ping interval
        startPingInterval()

        // Call onConnect callback
        onConnectRef.current?.()
      }

      ws.onmessage = (event) => {
        if (!mountedRef.current) return

        const parsed = parseMessage(event.data)
        if (parsed) {
          setLastMessage(parsed)
          onMessageRef.current?.(parsed)
        }
      }

      ws.onerror = (error) => {
        if (!mountedRef.current) return

        // WebSocket error occurred
        onErrorRef.current?.(error)
      }

      ws.onclose = (event) => {
        if (!mountedRef.current) return

        clearTimers()
        wsRef.current = null

        // Call onDisconnect callback
        onDisconnectRef.current?.(event)

        // Don't reconnect if manually disconnected or max attempts reached
        if (manualDisconnectRef.current) {
          setConnectionState('disconnected')
          return
        }

        // Handle reconnection
        if (reconnect && reconnectAttemptsCount < reconnectAttempts) {
          setConnectionState('reconnecting')
          setReconnectAttemptsCount((prev) => prev + 1)

          // Exponential backoff with jitter
          const jitter = Math.random() * 1000
          const nextInterval = Math.min(
            currentReconnectInterval.current * 2,
            maxReconnectInterval
          )
          currentReconnectInterval.current = nextInterval

          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current && !manualDisconnectRef.current) {
              connect()
            }
          }, currentReconnectInterval.current + jitter)
        } else if (reconnectAttemptsCount >= reconnectAttempts) {
          setConnectionState('disconnected')
        } else {
          setConnectionState('disconnected')
        }
      }
    } catch (error) {
      // Failed to create WebSocket connection
      setConnectionState('disconnected')
    }
  }, [
    url,
    token,
    reconnect,
    reconnectInterval,
    maxReconnectInterval,
    reconnectAttempts,
    reconnectAttemptsCount,
    clearTimers,
    startPingInterval,
  ])

  /**
   * Sends a message to the server.
   */
  const send = useCallback((message: ClientMessage) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      return
    }

    wsRef.current.send(JSON.stringify(message))
  }, [])

  /**
   * Subscribe to schedule updates.
   */
  const subscribeToSchedule = useCallback((scheduleId: string) => {
    send({ action: 'subscribe_schedule', scheduleId: scheduleId })
  }, [send])

  /**
   * Unsubscribe from schedule updates.
   */
  const unsubscribeFromSchedule = useCallback((scheduleId: string) => {
    send({ action: 'unsubscribe_schedule', scheduleId: scheduleId })
  }, [send])

  /**
   * Subscribe to person updates.
   */
  const subscribeToPerson = useCallback((personId: string) => {
    send({ action: 'subscribe_person', personId: personId })
  }, [send])

  /**
   * Unsubscribe from person updates.
   */
  const unsubscribeFromPerson = useCallback((personId: string) => {
    send({ action: 'unsubscribe_person', personId: personId })
  }, [send])

  // Auto-connect on mount
  useEffect(() => {
    mountedRef.current = true

    if (autoConnect) {
      connect()
    }

    return () => {
      mountedRef.current = false
      clearTimers()
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount')
        wsRef.current = null
      }
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return {
    connectionState,
    isConnected: connectionState === 'connected',
    lastMessage,
    reconnectAttempts: reconnectAttemptsCount,
    send,
    connect,
    disconnect,
    subscribeToSchedule,
    unsubscribeFromSchedule,
    subscribeToPerson,
    unsubscribeFromPerson,
  }
}

// ============================================================================
// Specialized Hooks
// ============================================================================

/**
 * Hook for subscribing to schedule-specific events.
 *
 * @param scheduleId - The schedule ID to subscribe to
 * @param options - WebSocket options
 * @returns WebSocket state with schedule subscription
 *
 * @example
 * ```tsx
 * function ScheduleView({ scheduleId }: { scheduleId: string }) {
 *   const { isConnected, lastMessage } = useScheduleWebSocket(scheduleId, {
 *     onMessage: (event) => {
 *       if (event.eventType === 'schedule_updated') {
 *         queryClient.invalidateQueries({ queryKey: ['schedule'] });
 *       }
 *     }
 *   });
 *
 *   return <ScheduleGrid scheduleId={scheduleId} />;
 * }
 * ```
 */
export function useScheduleWebSocket(
  scheduleId: string | undefined,
  options: Omit<UseWebSocketOptions, 'autoConnect'> = {}
): UseWebSocketReturn {
  const ws = useWebSocket({ ...options, autoConnect: true })

  useEffect(() => {
    if (ws.isConnected && scheduleId) {
      ws.subscribeToSchedule(scheduleId)
      return () => {
        ws.unsubscribeFromSchedule(scheduleId)
      }
    }
  }, [ws.isConnected, scheduleId]) // eslint-disable-line react-hooks/exhaustive-deps

  return ws
}

/**
 * Hook for subscribing to person-specific events.
 *
 * @param personId - The person ID to subscribe to
 * @param options - WebSocket options
 * @returns WebSocket state with person subscription
 *
 * @example
 * ```tsx
 * function PersonDetail({ personId }: { personId: string }) {
 *   const { isConnected, lastMessage } = usePersonWebSocket(personId, {
 *     onMessage: (event) => {
 *       if (event.eventType === 'assignment_changed') {
 *         toast.info('Your schedule has been updated');
 *       }
 *     }
 *   });
 *
 *   return <PersonSchedule personId={personId} />;
 * }
 * ```
 */
export function usePersonWebSocket(
  personId: string | undefined,
  options: Omit<UseWebSocketOptions, 'autoConnect'> = {}
): UseWebSocketReturn {
  const ws = useWebSocket({ ...options, autoConnect: true })

  useEffect(() => {
    if (ws.isConnected && personId) {
      ws.subscribeToPerson(personId)
      return () => {
        ws.unsubscribeFromPerson(personId)
      }
    }
  }, [ws.isConnected, personId]) // eslint-disable-line react-hooks/exhaustive-deps

  return ws
}

// Default export
export default useWebSocket
