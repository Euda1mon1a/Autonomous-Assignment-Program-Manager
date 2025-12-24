import React, { createContext, useContext, ReactNode } from 'react';
import { useClaudeChat } from '../hooks/useClaudeChat';
import { ChatMessage, ChatSession } from '../types/chat';

interface ClaudeChatContextType {
  session: ChatSession | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  initializeSession: (programId: string, adminId: string, title?: string) => ChatSession;
  sendMessage: (userInput: string, context?: any, onStreamUpdate?: any) => Promise<void>;
  cancelRequest: () => void;
  clearMessages: () => void;
  exportSession: () => any;
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
