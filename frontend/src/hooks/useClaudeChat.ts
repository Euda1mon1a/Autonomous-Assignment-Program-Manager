import { useState, useCallback, useRef, useEffect } from 'react';
import { ChatMessage, ChatSession, ClaudeCodeRequest, ClaudeCodeResponse, StreamUpdate } from '../types/chat';
import { v4 as uuidv4 } from 'uuid';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const CLAUDE_CHAT_ENDPOINT = `${API_BASE_URL}/api/claude/chat`;
const CLAUDE_STREAM_ENDPOINT = `${API_BASE_URL}/api/claude/chat/stream`;

export const useClaudeChat = () => {
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

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
      return newSession;
    },
    []
  );

  // Send message to Claude with streaming
  const sendMessage = useCallback(
    async (
      userInput: string,
      context?: any,
      onStreamUpdate?: (update: StreamUpdate) => void
    ) => {
      if (!session) {
        setError('No active session');
        return;
      }

      if (!userInput.trim()) return;

      // Add user message
      const userMessage: ChatMessage = {
        id: uuidv4(),
        role: 'user',
        content: userInput,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
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

      setMessages((prev) => [...prev, assistantMessage]);

      try {
        // Abort previous request if any
        if (abortControllerRef.current) {
          abortControllerRef.current.abort();
        }
        abortControllerRef.current = new AbortController();

        const request: ClaudeCodeRequest = {
          action: 'custom',
          context: {
            programId: session.programId,
            adminId: session.adminId,
            sessionId: session.id,
            ...context,
          },
          userQuery: userInput,
        };

        const response = await fetch(CLAUDE_STREAM_ENDPOINT, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify(request),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error('No response body');

        const decoder = new TextDecoder();
        let fullContent = '';
        let codeBlocks: any[] = [];
        let artifacts: any[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6)) as StreamUpdate;
                fullContent += data.content;

                if (data.type === 'code') {
                  codeBlocks.push(data.metadata);
                } else if (data.type === 'artifact') {
                  artifacts.push(data.metadata);
                }

                onStreamUpdate?.(data);

                // Update assistant message in real-time
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessage.id
                      ? {
                          ...msg,
                          content: fullContent,
                          codeBlocks,
                          artifacts,
                        }
                      : msg
                  )
                );
              } catch (e) {
                // Continue on JSON parse error
              }
            }
          }
        }

        // Finalize assistant message
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessage.id
              ? {
                  ...msg,
                  isStreaming: false,
                  content: fullContent || 'Processing complete.',
                  codeBlocks,
                  artifacts,
                }
              : msg
          )
        );
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Unknown error occurred';
        setError(errorMessage);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessage.id
              ? {
                  ...msg,
                  isStreaming: false,
                  error: errorMessage,
                  content: `Error: ${errorMessage}`,
                }
              : msg
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [session]
  );

  // Cancel ongoing request
  const cancelRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
  }, []);

  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  // Export session
  const exportSession = useCallback(() => {
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
    initializeSession,
    sendMessage,
    cancelRequest,
    clearMessages,
    exportSession,
  };
};
