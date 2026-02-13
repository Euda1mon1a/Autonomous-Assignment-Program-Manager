import { renderHook, waitFor, act, createWrapper } from '@/test-utils';
import { useClaudeChat } from '@/hooks/useClaudeChat';

// Mock uuid and auth before any imports that use it
jest.mock('uuid', () => ({
  v4: () => 'test-uuid-1234',
}));

jest.mock('@/lib/auth', () => ({
  getAccessToken: () => 'test-token',
}));

let lastWebSocket: MockWebSocket | null = null;

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.OPEN;
  send = jest.fn();
  close = jest.fn();
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(public url: string) {
    lastWebSocket = this;
    setTimeout(() => {
      this.onopen?.();
    }, 0);
  }
}

describe('useClaudeChat', () => {
  beforeEach(() => {
    lastWebSocket = null;
    global.WebSocket = MockWebSocket as unknown as typeof WebSocket;
  });

  it('initializes a session and sends a message over WebSocket', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useClaudeChat(), { wrapper });

    act(() => {
      result.current.initializeSession('program-1', 'admin-1', 'Test Session');
    });

    await waitFor(() => {
      expect(result.current.session).not.toBeNull();
    });

    await act(async () => {
      await result.current.sendMessage('Hello Claude');
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2);
    });

    expect(result.current.messages[0]).toMatchObject({
      role: 'user',
      content: 'Hello Claude',
    });
    expect(result.current.messages[1]).toMatchObject({
      role: 'assistant',
    });
    expect(lastWebSocket?.send).toHaveBeenCalledWith(
      expect.stringContaining('"type":"user_message"')
    );
  });

  it('clears messages and error state', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useClaudeChat(), { wrapper });

    act(() => {
      result.current.initializeSession('program-1', 'admin-1', 'Test Session');
    });

    await act(async () => {
      await result.current.sendMessage('Hello Claude');
    });

    await waitFor(() => {
      expect(result.current.messages.length).toBeGreaterThan(0);
    });

    act(() => {
      result.current.clearMessages();
    });

    expect(result.current.messages).toHaveLength(0);
    expect(result.current.error).toBeNull();
  });
})
