import React, { createContext, useContext, ReactNode } from 'react';
import { useClaudeChat, SavedSession } from '../hooks/useClaudeChat';
import { ChatMessage, ChatSession, ClaudeCodeExecutionContext, StreamUpdate } from '../types/chat';

interface SessionExport {
  session: ChatSession;
  exportedAt: Date;
  version: string;
}

interface ClaudeChatContextType {
  session: ChatSession | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  initializeSession: (programId: string, adminId: string, title?: string) => ChatSession;
  sendMessage: (userInput: string, context?: Partial<ClaudeCodeExecutionContext>, onStreamUpdate?: (update: StreamUpdate) => void) => Promise<void>;
  cancelRequest: () => void;
  clearMessages: () => void;
  exportSession: () => SessionExport;
  getSavedSessions: () => SavedSession[];
  loadSession: (sessionId: string) => boolean;
}

const ClaudeChatContext = createContext<ClaudeChatContextType | undefined>(undefined);

export const ClaudeChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const chat = useClaudeChat();

  return (
    <ClaudeChatContext.Provider value={chat}>
      {children}
    </ClaudeChatContext.Provider>
  );
};

export const useClaudeChatContext = () => {
  const context = useContext(ClaudeChatContext);
  if (!context) {
    throw new Error('useClaudeChatContext must be used within ClaudeChatProvider');
  }
  return context;
};
