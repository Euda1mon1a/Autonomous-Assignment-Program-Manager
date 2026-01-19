import { useState, useCallback, useRef, useEffect } from 'react';
import { ChatMessage, ChatSession, StreamUpdate, CodeBlock, ChatArtifact, StreamMetadata } from '../types/chat';
import { getAccessToken } from '@/lib/auth';
import { v4 as uuidv4 } from 'uuid';

// WebSocket endpoint - connects to backend Claude chat bridge
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');
const CLAUDE_WS_ENDPOINT = `${WS_BASE_URL}/api/v1/claude-chat/ws`;

// localStorage keys
const STORAGE_KEY_SESSION = 'claude_chat_session';
const STORAGE_KEY_MESSAGES = 'claude_chat_messages';
const STORAGE_KEY_SESSIONS_LIST = 'claude_chat_sessions_list';

/**
 * Helper to safely parse dates from JSON.
 */
const reviveDates = (key: string, value: unknown): unknown => {
  if (typeof value === 'string') {
    const dateRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/;
    if (dateRegex.test(value)) {
      return new Date(value);
    }
  }
  return value;
};

// Helper to load from localStorage
const loadFromStorage = <T>(key: string): T | null => {
  try {
    const stored = localStorage.getItem(key);
    if (stored) {
      return JSON.parse(stored, reviveDates);
    }
  } catch {
    // Silent failure - localStorage may be unavailable
  }
  return null;
};

/**
 * Helper to save data to localStorage.
 */
const saveToStorage = (key: string, value: unknown): void => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Silent failure - localStorage may be full or unavailable
  }
};

/**
 * Context data for Claude Code requests.
 */
export interface ClaudeCodeContext {
  programId: string;
  adminId: string;
  sessionId: string;
  [key: string]: unknown;
}

/**
 * Helper function to extract CodeBlock from streaming metadata.
 * Kept for potential future use with tool results.
 */
function _extractCodeBlock(content: string, metadata?: StreamMetadata): CodeBlock | null {
  if (!metadata) return null;
  return {
    language: typeof metadata.language === 'string' ? metadata.language : 'text',
    code: content,
    filename: typeof metadata.filename === 'string' ? metadata.filename : undefined,
  };
}

/**
 * Infer artifact type from tool name.
 * Used to categorize tool results for UI display.
 */
function inferArtifactType(toolName?: string): ChatArtifact['type'] {
  if (!toolName) return 'report';
  const name = toolName.toLowerCase();
  if (name.includes('schedule') || name.includes('assignment')) return 'schedule';
  if (name.includes('analysis') || name.includes('validate') || name.includes('check')) return 'analysis';
  if (name.includes('config') || name.includes('setting')) return 'configuration';
  return 'report';
}

/**
 * Helper function to extract ChatArtifact from streaming data.
 * Kept for potential future use with tool results.
 */
function _extractArtifact(content: string, metadata?: StreamMetadata): ChatArtifact | null {
  if (!metadata) return null;
  const artifactType = typeof metadata.type === 'string' ? metadata.type : 'configuration';
  const validTypes = ['schedule', 'analysis', 'report', 'configuration'] as const;
  const type = validTypes.includes(artifactType as typeof validTypes[number])
    ? (artifactType as typeof validTypes[number])
    : 'configuration';

  return {
    id: `artifact-${Date.now()}`,
    type,
    title: typeof metadata.title === 'string' ? metadata.title : 'Artifact',
    data: { content },
    createdAt: new Date(),
  };
}

/**
 * Error types for Claude Chat operations.
 */
export type ClaudeChatErrorType =
  | 'NO_SESSION'
  | 'EMPTY_MESSAGE'
  | 'NETWORK_ERROR'
  | 'WEBSOCKET_ERROR'
  | 'AUTH_ERROR'
  | 'STREAM_ERROR'
  | 'PARSE_ERROR'
  | 'ABORT_ERROR'
  | 'UNKNOWN_ERROR';

/**
 * Structured error for Claude Chat operations.
 */
export interface ClaudeChatError {
  type: ClaudeChatErrorType;
  message: string;
  originalError?: Error;
  timestamp: Date;
}

export interface SavedSession {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  programId: string;
}

/**
 * WebSocket message types from backend
 */
interface WsConnectedMessage {
  type: 'connected';
  session_id: string;
  history_count: number;
}

interface WsTokenMessage {
  type: 'token';
  content: string;
}

interface WsToolCallMessage {
  type: 'tool_call' | 'tool_call_start';
  name: string;
  input?: Record<string, unknown>;
  id: string;
}

interface WsToolResultMessage {
  type: 'tool_result';
  id: string;
  result: Record<string, unknown>;
}

interface WsCompleteMessage {
  type: 'complete';
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

interface WsErrorMessage {
  type: 'error';
  message: string;
}

interface WsInterruptedMessage {
  type: 'interrupted';
  message: string;
  partial_response?: boolean;
}

interface WsHistoryMessage {
  type: 'history';
  messages: Array<{
    role: string;
    content: string;
    timestamp: string;
    tool_calls?: Array<Record<string, unknown>>;
  }>;
}

type WsMessage =
  | WsConnectedMessage
  | WsTokenMessage
  | WsToolCallMessage
  | WsToolResultMessage
  | WsCompleteMessage
  | WsErrorMessage
  | WsInterruptedMessage
  | WsHistoryMessage;

/**
 * WebSocket connection state
 */
type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';

export const useClaudeChat = () => {
  // Load initial state from localStorage
  const [session, setSession] = useState<ChatSession | null>(() =>
    loadFromStorage<ChatSession>(STORAGE_KEY_SESSION)
  );
  const [messages, setMessages] = useState<ChatMessage[]>(() =>
    loadFromStorage<ChatMessage[]>(STORAGE_KEY_MESSAGES) || []
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');

  // WebSocket refs
  const wsRef = useRef<WebSocket | null>(null);
  const currentAssistantMessageIdRef = useRef<string | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const handleWsMessageRef = useRef<((data: WsMessage) => void) | null>(null);
  const onStreamUpdateRef = useRef<((update: StreamUpdate) => void) | null>(null);

  // Persist session to localStorage when it changes
  useEffect(() => {
    if (session) {
      saveToStorage(STORAGE_KEY_SESSION, session);
      updateSessionsList(session, messages.length);
    }
  }, [session, messages.length]);

  // Persist messages to localStorage when they change
  useEffect(() => {
    saveToStorage(STORAGE_KEY_MESSAGES, messages);
    if (session && messages.length > 0) {
      updateSessionsList({ ...session, updatedAt: new Date() }, messages.length);
    }
  }, [messages, session]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  // Update sessions list for session history
  const updateSessionsList = (currentSession: ChatSession, messageCount: number): void => {
    const sessionsList = loadFromStorage<SavedSession[]>(STORAGE_KEY_SESSIONS_LIST) || [];
    const existingIndex = sessionsList.findIndex(s => s.id === currentSession.id);

    const savedSession: SavedSession = {
      id: currentSession.id,
      title: currentSession.title,
      createdAt: currentSession.createdAt,
      updatedAt: new Date(),
      messageCount,
      programId: currentSession.programId,
    };

    if (existingIndex >= 0) {
      sessionsList[existingIndex] = savedSession;
    } else {
      sessionsList.unshift(savedSession);
    }

    const trimmedList = sessionsList.slice(0, 20);
    saveToStorage(STORAGE_KEY_SESSIONS_LIST, trimmedList);
  };

  /**
   * Connect to WebSocket
   */
  const connect = useCallback((sessionId?: string) => {
    // Don't connect if already connected or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN ||
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setError('Not authenticated. Please log in.');
      setConnectionState('error');
      return;
    }

    setConnectionState('connecting');

    // Build WebSocket URL with query params
    const wsUrl = new URL(CLAUDE_WS_ENDPOINT);
    wsUrl.searchParams.set('token', token);
    if (sessionId) {
      wsUrl.searchParams.set('session_id', sessionId);
    }

    console.log('[useClaudeChat] Connecting to WebSocket:', wsUrl.toString().replace(token, '***'));

    const ws = new WebSocket(wsUrl.toString());
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[useClaudeChat] WebSocket connected');
      setConnectionState('connected');
      setError(null);
    };

    ws.onclose = (event) => {
      console.log('[useClaudeChat] WebSocket closed:', event.code, event.reason);
      setConnectionState('disconnected');
      wsRef.current = null;

      // Auto-reconnect after 3 seconds if not intentional close
      if (event.code !== 1000 && event.code !== 4001 && event.code !== 4003) {
        reconnectTimeoutRef.current = setTimeout(() => {
          if (session) {
            connect(session.id);
          }
        }, 3000);
      }
    };

    ws.onerror = (event) => {
      console.error('[useClaudeChat] WebSocket error:', event);
      setConnectionState('error');
      setError('WebSocket connection failed');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsMessage;
        // Use ref to get latest handler without stale closure
        handleWsMessageRef.current?.(data);
      } catch (e) {
        console.error('[useClaudeChat] Failed to parse message:', e);
      }
    };
  }, [session]);

  /**
   * Handle incoming WebSocket messages
   */
  const handleWsMessage = useCallback((data: WsMessage) => {
    switch (data.type) {
      case 'connected':
        console.log('[useClaudeChat] Session connected:', data.session_id);
        // Update session ID if we got a new one from server
        setSession(prev => prev ? { ...prev, id: data.session_id } : prev);
        break;

      case 'token': {
        // Streaming token - update assistant message content
        const messageId = currentAssistantMessageIdRef.current;
        if (messageId) {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === messageId
                ? { ...msg, content: msg.content + data.content }
                : msg
            )
          );
        }
        break;
      }

      case 'tool_call_start':
      case 'tool_call': {
        // Tool being executed - could add to UI
        console.log('[useClaudeChat] Tool call:', data.name, data.input);
        break;
      }

      case 'tool_result': {
        // Tool result - surface to UI as artifact and notify callback
        console.log('[useClaudeChat] Tool result:', data.id, data.result);

        // Extract tool name from result if available, otherwise use generic title
        const resultData = data.result || {};
        const toolTitle = (resultData.tool_name as string) || `Tool Result (${data.id.slice(0, 8)})`;

        // Create artifact from tool result
        const artifact: ChatArtifact = {
          id: data.id || uuidv4(),
          type: inferArtifactType(toolTitle),
          title: toolTitle,
          data: resultData,
          createdAt: new Date(),
        };

        // Add artifact to current assistant message
        const messageId = currentAssistantMessageIdRef.current;
        if (messageId) {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === messageId
                ? { ...msg, artifacts: [...(msg.artifacts || []), artifact] }
                : msg
            )
          );
        }

        // Notify stream update callback (used by ClaudeCodeChat for artifact handling)
        if (onStreamUpdateRef.current) {
          onStreamUpdateRef.current({
            type: 'artifact',
            content: toolTitle,
            metadata: {
              id: artifact.id,
              type: artifact.type,
              title: artifact.title,
              createdAt: artifact.createdAt.toISOString(),
            },
          });
        }
        break;
      }

      case 'complete': {
        // Generation complete
        const messageId = currentAssistantMessageIdRef.current;
        if (messageId) {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === messageId
                ? { ...msg, isStreaming: false }
                : msg
            )
          );
        }
        currentAssistantMessageIdRef.current = null;
        setIsLoading(false);
        console.log('[useClaudeChat] Complete:', data.usage);
        break;
      }

      case 'interrupted': {
        // Generation interrupted
        const messageId = currentAssistantMessageIdRef.current;
        if (messageId) {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === messageId
                ? { ...msg, isStreaming: false, content: msg.content + ' [interrupted]' }
                : msg
            )
          );
        }
        currentAssistantMessageIdRef.current = null;
        setIsLoading(false);
        console.log('[useClaudeChat] Interrupted:', data.message);
        break;
      }

      case 'error': {
        // Error occurred
        const messageId = currentAssistantMessageIdRef.current;
        if (messageId) {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === messageId
                ? { ...msg, isStreaming: false, error: data.message, content: `Error: ${data.message}` }
                : msg
            )
          );
        }
        currentAssistantMessageIdRef.current = null;
        setIsLoading(false);
        setError(data.message);
        console.error('[useClaudeChat] Error:', data.message);
        break;
      }

      case 'history': {
        // Session history received
        console.log('[useClaudeChat] History received:', data.messages.length, 'messages');
        break;
      }
    }
  }, []);

  // Keep the ref updated with latest handler to avoid stale closures
  useEffect(() => {
    handleWsMessageRef.current = handleWsMessage;
  }, [handleWsMessage]);

  // Get list of saved sessions
  const getSavedSessions = useCallback((): SavedSession[] => {
    return loadFromStorage<SavedSession[]>(STORAGE_KEY_SESSIONS_LIST) || [];
  }, []);

  // Load a previous session
  const loadSession = useCallback((sessionId: string): boolean => {
    const storedSession = loadFromStorage<ChatSession>(STORAGE_KEY_SESSION);
    if (storedSession && storedSession.id === sessionId) {
      setSession(storedSession);
      setMessages(loadFromStorage<ChatMessage[]>(STORAGE_KEY_MESSAGES) || []);
      // Reconnect with this session ID
      connect(sessionId);
      return true;
    }
    return false;
  }, [connect]);

  // Initialize new session
  const initializeSession = useCallback(
    (programId: string, adminId: string, title: string = 'Claude Code Chat') => {
      const newSession: ChatSession = {
        id: uuidv4(),
        title,
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        programId,
        adminId,
      };
      setSession(newSession);
      setMessages([]);
      setError(null);

      // Connect WebSocket for new session
      connect(newSession.id);

      return newSession;
    },
    [connect]
  );

  /**
   * Send message to Claude via WebSocket.
   */
  const sendMessage = useCallback(
    async (
      userInput: string,
      _context?: Partial<ClaudeCodeContext>,
      _onStreamUpdate?: (update: StreamUpdate) => void
    ) => {
      if (!session) {
        setError('No active session');
        return;
      }

      if (!userInput.trim()) {
        setError('Message cannot be empty');
        return;
      }

      // Store stream update callback for use in message handler
      onStreamUpdateRef.current = _onStreamUpdate || null;

      // Ensure WebSocket is connected
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.log('[useClaudeChat] Connecting before send...');
        connect(session.id);
        // Wait a bit for connection
        await new Promise(resolve => setTimeout(resolve, 1000));

        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          setError('Failed to connect to chat server');
          return;
        }
      }

      // Add user message
      const userMessage: ChatMessage = {
        id: uuidv4(),
        role: 'user',
        content: userInput,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      // Create assistant message placeholder
      const assistantMessage: ChatMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      };

      currentAssistantMessageIdRef.current = assistantMessage.id;
      setMessages(prev => [...prev, assistantMessage]);

      // Send message via WebSocket
      wsRef.current.send(JSON.stringify({
        type: 'user_message',
        content: userInput,
        session_id: session.id,
      }));
    },
    [session, connect]
  );

  // Cancel/interrupt ongoing request
  const cancelRequest = useCallback((): void => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'interrupt' }));
    }
    setIsLoading(false);
  }, []);

  // Clear messages
  const clearMessages = useCallback((): void => {
    setMessages([]);
    setError(null);
  }, []);

  // Disconnect WebSocket
  const disconnect = useCallback((): void => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    setConnectionState('disconnected');
  }, []);

  // Export session
  const exportSession = useCallback((): (ChatSession & { messages: ChatMessage[] }) | null => {
    if (!session) return null;
    return {
      ...session,
      messages,
    };
  }, [session, messages]);

  return {
    session,
    messages,
    isLoading,
    error,
    connectionState,
    initializeSession,
    sendMessage,
    cancelRequest,
    clearMessages,
    exportSession,
    getSavedSessions,
    loadSession,
    connect,
    disconnect,
  };
};
