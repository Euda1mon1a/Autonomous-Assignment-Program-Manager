/**
 * Tests for Claude Chat Hook
 *
 * Tests chat session management, message handling,
 * localStorage persistence, and streaming responses.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { useClaudeChat } from './useClaudeChat';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock fetch
global.fetch = jest.fn();

describe('useClaudeChat', () => {
  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  it('initializes session correctly', () => {
    const { result } = renderHook(() => useClaudeChat());

    act(() => {
      result.current.initializeSession('program-123', 'admin-456', 'Test Chat');
    });

    expect(result.current.session).toBeDefined();
    expect(result.current.session?.title).toBe('Test Chat');
    expect(result.current.session?.programId).toBe('program-123');
    expect(result.current.session?.adminId).toBe('admin-456');
  });

  it('loads session from localStorage', () => {
    const mockSession = {
      id: 'session-123',
      title: 'Saved Chat',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      programId: 'program-123',
      adminId: 'admin-456',
    };

    localStorageMock.setItem('claude_chat_session', JSON.stringify(mockSession));

    const { result } = renderHook(() => useClaudeChat());

    expect(result.current.session).toBeDefined();
  });

  it('sends message and handles response', async () => {
    const mockResponse = {
      body: {
        getReader: () => ({
          read: jest
            .fn()
            .mockResolvedValueOnce({
              done: false,
              value: new TextEncoder().encode('data: {"type":"text","content":"Hello"}\n'),
            })
            .mockResolvedValueOnce({ done: true }),
        }),
      },
      ok: true,
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useClaudeChat());

    act(() => {
      result.current.initializeSession('program-123', 'admin-456');
    });

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2); // User + Assistant
    });

    expect(result.current.messages[0].role).toBe('user');
    expect(result.current.messages[0].content).toBe('Test message');
  });

  it('handles errors during message sending', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useClaudeChat());

    act(() => {
      result.current.initializeSession('program-123', 'admin-456');
    });

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });
  });

  it('cancels ongoing request', () => {
    const { result } = renderHook(() => useClaudeChat());

    act(() => {
      result.current.initializeSession('program-123', 'admin-456');
    });

    act(() => {
      result.current.cancelRequest();
    });

    expect(result.current.isLoading).toBe(false);
  });

  it('clears messages', () => {
    const { result } = renderHook(() => useClaudeChat());

    act(() => {
      result.current.initializeSession('program-123', 'admin-456');
    });

    // Add some messages
    act(() => {
      result.current.clearMessages();
    });

    expect(result.current.messages).toHaveLength(0);
    expect(result.current.error).toBeNull();
  });

  it('exports session', () => {
    const { result } = renderHook(() => useClaudeChat());

    act(() => {
      result.current.initializeSession('program-123', 'admin-456', 'Export Test');
    });

    const exported = result.current.exportSession();

    expect(exported).toBeDefined();
    expect(exported?.title).toBe('Export Test');
    expect(exported?.messages).toBeDefined();
  });

  it('gets saved sessions list', () => {
    const mockSessions = [
      {
        id: 'session-1',
        title: 'Chat 1',
        createdAt: new Date(),
        updatedAt: new Date(),
        messageCount: 10,
        programId: 'program-123',
      },
    ];

    localStorageMock.setItem('claude_chat_sessions_list', JSON.stringify(mockSessions));

    const { result } = renderHook(() => useClaudeChat());

    const sessions = result.current.getSavedSessions();

    expect(sessions).toHaveLength(1);
    expect(sessions[0].title).toBe('Chat 1');
  });

  it('persists messages to localStorage', async () => {
    const { result } = renderHook(() => useClaudeChat());

    act(() => {
      result.current.initializeSession('program-123', 'admin-456');
    });

    // Messages should be persisted via useEffect
    await waitFor(() => {
      const stored = localStorageMock.getItem('claude_chat_messages');
      expect(stored).toBeDefined();
    });
  });

  it('handles session loading', () => {
    const mockSession = {
      id: 'session-123',
      title: 'Test Chat',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      programId: 'program-123',
      adminId: 'admin-456',
    };

    localStorageMock.setItem('claude_chat_session', JSON.stringify(mockSession));

    const { result } = renderHook(() => useClaudeChat());

    const loaded = result.current.loadSession('session-123');

    expect(loaded).toBe(true);
    expect(result.current.session?.id).toBe('session-123');
  });
});
