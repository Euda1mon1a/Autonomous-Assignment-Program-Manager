import React, { createContext, useContext, ReactNode } from 'react';
import { useClaudeChat, SavedSession, ClaudeCodeContext } from '../hooks/useClaudeChat';
import { ChatMessage, ChatSession, StreamUpdate } from '../types/chat';

/**
 * Exported session data structure.
 */
interface ExportedSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
  programId: string;
  adminId: string;
}

/**
 * Claude Chat context type providing chat functionality to components.
 */
interface ClaudeChatContextType {
  session: ChatSession | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  initializeSession: (programId: string, adminId: string, title?: string) => ChatSession;
  sendMessage: (userInput: string, context?: Partial<ClaudeCodeContext>, onStreamUpdate?: (update: StreamUpdate) => void) => Promise<void>;
  cancelRequest: () => void;
  clearMessages: () => void;
  exportSession: () => ExportedSession | null;
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
