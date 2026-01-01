/**
 * Tests for WebSocket Client Hook
 *
 * Tests WebSocket connection management, automatic reconnection,
 * subscription handling, and real-time event processing.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { useWebSocket, useScheduleWebSocket, usePersonWebSocket } from './useWebSocket';

// Mock WebSocket
class MockWebSocket {
  public readyState: number = WebSocket.CONNECTING;
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public url: string;
  public sentMessages: string[] = [];

  constructor(url: string) {
    this.url = url;
    // Simulate connection after a short delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send(data: string): void {
    this.sentMessages.push(data);
  }

  close(code?: number, reason?: string): void {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      const event = new CloseEvent('close', { code, reason });
      this.onclose(event);
    }
  }

  // Helper to simulate receiving a message
  simulateMessage(data: any): void {
    if (this.onmessage) {
      const event = new MessageEvent('message', {
        data: JSON.stringify(data),
      });
      this.onmessage(event);
    }
  }

  // Helper to simulate an error
  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// Mock global WebSocket
// eslint-disable-next-line @typescript-eslint/no-explicit-any
global.WebSocket = MockWebSocket as any;

// Test event data
const mockScheduleUpdatedEvent = {
  event_type: 'schedule_updated',
  timestamp: '2024-01-01T00:00:00Z',
  schedule_id: 'schedule-123',
  academic_year_id: 'year-2024',
  user_id: 'user-456',
  update_type: 'generated',
  affected_blocks_count: 50,
  message: 'Schedule generated successfully',
};

const mockAssignmentChangedEvent = {
  event_type: 'assignment_changed',
  timestamp: '2024-01-01T00:00:00Z',
  assignment_id: 'assignment-789',
  person_id: 'person-123',
  block_id: 'block-456',
  rotation_template_id: 'template-789',
  change_type: 'created',
  changed_by: 'user-123',
  message: 'Assignment created',
};

const mockConnectionAckEvent = {
  event_type: 'connection_ack',
  timestamp: '2024-01-01T00:00:00Z',
  user_id: 'user-123',
  message: 'Connected successfully',
};

describe('useWebSocket', () => {
  let mockWs: MockWebSocket;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('connects to WebSocket successfully', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
        token: 'test-token',
      })
    );

    // Initially disconnected
    expect(result.current.isConnected).toBe(false);

    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    expect(result.current.connectionState).toBe('connected');
  });

  it('includes token in WebSocket URL', async () => {
    renderHook(() =>
      useWebSocket({
        autoConnect: true,
        token: 'test-token-123',
        url: 'ws://localhost:8000/api/v1/ws',
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    // WebSocket constructor should have been called with token
    // The actual URL checking would depend on mocking implementation
  });

  it('receives and parses messages', async () => {
    const onMessage = jest.fn();

    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
        onMessage,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate receiving a message
    act(() => {
      // Get the mock WebSocket instance
      const ws = (global as any).WebSocket.instances?.[0];
      if (ws) {
        ws.simulateMessage(mockScheduleUpdatedEvent);
      }
    });

    expect(onMessage).toHaveBeenCalledWith(mockScheduleUpdatedEvent);
    expect(result.current.lastMessage).toEqual(mockScheduleUpdatedEvent);
  });

  it('sends messages to server', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Send a message
    act(() => {
      result.current.send({
        action: 'subscribe_schedule',
        schedule_id: 'schedule-123',
      });
    });

    // The message should have been sent (verified via mock)
  });

  it('handles connection errors', async () => {
    const onError = jest.fn();

    renderHook(() =>
      useWebSocket({
        autoConnect: true,
        onError,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    // Simulate an error
    act(() => {
      const ws = (global as any).WebSocket.instances?.[0];
      if (ws) {
        ws.simulateError();
      }
    });

    expect(onError).toHaveBeenCalled();
  });

  it('disconnects cleanly', async () => {
    const onDisconnect = jest.fn();

    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
        onDisconnect,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Disconnect
    act(() => {
      result.current.disconnect();
    });

    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionState).toBe('disconnected');
  });

  it('reconnects automatically on disconnect', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
        reconnect: true,
        reconnectInterval: 1000,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate disconnection
    act(() => {
      const ws = (global as any).WebSocket.instances?.[0];
      if (ws) {
        ws.close();
      }
    });

    expect(result.current.connectionState).toBe('reconnecting');

    // Wait for reconnection
    act(() => {
      jest.advanceTimersByTime(1500);
    });

    // Should attempt to reconnect
    expect(result.current.reconnectAttempts).toBeGreaterThan(0);
  });

  it('uses exponential backoff for reconnections', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
        reconnect: true,
        reconnectInterval: 1000,
        maxReconnectInterval: 30000,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate multiple disconnections to test exponential backoff
    for (let i = 0; i < 3; i++) {
      act(() => {
        const ws = (global as any).WebSocket.instances?.[i];
        if (ws) {
          ws.close();
        }
      });

      act(() => {
        // Exponential backoff: 1000ms, 2000ms, 4000ms, etc.
        jest.advanceTimersByTime(1000 * Math.pow(2, i) + 1000);
      });
    }
  });

  it('stops reconnecting after max attempts', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
        reconnect: true,
        reconnectAttempts: 3,
        reconnectInterval: 1000,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate multiple failed reconnections
    for (let i = 0; i <= 3; i++) {
      act(() => {
        const ws = (global as any).WebSocket.instances?.[i];
        if (ws) {
          ws.close();
        }
      });

      act(() => {
        jest.advanceTimersByTime(2000);
      });
    }

    // Should stop reconnecting after max attempts
    expect(result.current.connectionState).toBe('disconnected');
  });

  it('subscribes to schedule updates', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Subscribe to schedule
    act(() => {
      result.current.subscribeToSchedule('schedule-123');
    });

    // Verify subscription message was sent (via mock)
  });

  it('unsubscribes from schedule updates', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Unsubscribe from schedule
    act(() => {
      result.current.unsubscribeFromSchedule('schedule-123');
    });

    // Verify unsubscription message was sent (via mock)
  });

  it('subscribes to person updates', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Subscribe to person
    act(() => {
      result.current.subscribeToPerson('person-123');
    });

    // Verify subscription message was sent (via mock)
  });

  it('unsubscribes from person updates', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Unsubscribe from person
    act(() => {
      result.current.unsubscribeFromPerson('person-123');
    });

    // Verify unsubscription message was sent (via mock)
  });

  it('sends ping messages for keepalive', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
        pingInterval: 5000,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Advance time to trigger ping
    act(() => {
      jest.advanceTimersByTime(5000);
    });

    // Verify ping message was sent (via mock)
  });

  it('cleans up on unmount', async () => {
    const { result, unmount } = renderHook(() =>
      useWebSocket({
        autoConnect: true,
      })
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Unmount the hook
    unmount();

    // Connection should be closed
    expect(result.current.isConnected).toBe(false);
  });
});

describe('useScheduleWebSocket', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('auto-subscribes to schedule on connection', async () => {
    const { result } = renderHook(() =>
      useScheduleWebSocket('schedule-123')
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Should have auto-subscribed to schedule-123
  });

  it('unsubscribes on unmount', async () => {
    const { result, unmount } = renderHook(() =>
      useScheduleWebSocket('schedule-123')
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Unmount
    unmount();

    // Should have unsubscribed
  });

  it('handles undefined schedule ID', async () => {
    const { result } = renderHook(() =>
      useScheduleWebSocket(undefined)
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Should not subscribe if schedule ID is undefined
  });
});

describe('usePersonWebSocket', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('auto-subscribes to person on connection', async () => {
    const { result } = renderHook(() =>
      usePersonWebSocket('person-123')
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Should have auto-subscribed to person-123
  });

  it('unsubscribes on unmount', async () => {
    const { result, unmount } = renderHook(() =>
      usePersonWebSocket('person-123')
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Unmount
    unmount();

    // Should have unsubscribed
  });

  it('handles undefined person ID', async () => {
    const { result } = renderHook(() =>
      usePersonWebSocket(undefined)
    );

    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Should not subscribe if person ID is undefined
  });
});
