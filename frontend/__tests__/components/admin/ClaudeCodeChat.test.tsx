/**
 * Tests for ClaudeCodeChat component
 *
 * Tests chat interface, message display, streaming, artifacts, and interactions
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ClaudeCodeChat from '@/components/admin/ClaudeCodeChat';
import { ClaudeChatProvider } from '@/contexts/ClaudeChatContext';
import { ChatMessage } from '@/types/chat';

// Mock the ClaudeChatContext hook
const mockInitializeSession = jest.fn();
const mockSendMessage = jest.fn();
const mockCancelRequest = jest.fn();
const mockClearMessages = jest.fn();

jest.mock('@/contexts/ClaudeChatContext', () => ({
  ClaudeChatProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useClaudeChatContext: () => ({
    session: { id: 'test-session', title: 'Test Session' },
    messages: [],
    isLoading: false,
    error: null,
    initializeSession: mockInitializeSession,
    sendMessage: mockSendMessage,
    cancelRequest: mockCancelRequest,
    clearMessages: mockClearMessages,
    exportSession: jest.fn(),
    getSavedSessions: jest.fn(() => []),
    loadSession: jest.fn(),
  }),
}));

describe('ClaudeCodeChat', () => {
  const defaultProps = {
    programId: 'prog-123',
    adminId: 'admin-456',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render chat header', () => {
      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('Claude Code Assistant')).toBeInTheDocument();
    });

    it('should show ready status when not loading and no error', () => {
      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('Ready')).toBeInTheDocument();
    });

    it('should render chat input form', () => {
      render(<ClaudeCodeChat {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(
        /Ask me anything about scheduling/i
      );
      expect(textarea).toBeInTheDocument();
    });

    it('should render send button', () => {
      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });

    it('should render clear button', () => {
      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should display empty state when no messages', () => {
      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('Start a conversation')).toBeInTheDocument();
      expect(
        screen.getByText(/Ask me to help with schedule generation/i)
      ).toBeInTheDocument();
    });

    it('should display quick prompt buttons in empty state', () => {
      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('Generate Schedule')).toBeInTheDocument();
      expect(screen.getByText('Check Compliance')).toBeInTheDocument();
      expect(screen.getByText('Export Report')).toBeInTheDocument();
    });

    it('should populate input when quick prompt is clicked', async () => {
      const user = userEvent.setup();
      render(<ClaudeCodeChat {...defaultProps} />);

      const generateButton = screen.getByText('Generate Schedule');
      await user.click(generateButton);

      const textarea = screen.getByPlaceholderText(
        /Ask me anything about scheduling/i
      ) as HTMLTextAreaElement;
      expect(textarea.value).toBe('Generate the schedule for the next rotation block');
    });
  });

  describe('Session Initialization', () => {
    it('should initialize session on mount when no session exists', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      mockUseContext.mockReturnValue({
        session: null,
        messages: [],
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(mockInitializeSession).toHaveBeenCalledWith(
        'prog-123',
        'admin-456',
        'Schedule Assistant'
      );
    });
  });

  describe('Message Sending', () => {
    it('should send message when form is submitted', async () => {
      const user = userEvent.setup();
      render(<ClaudeCodeChat {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(
        /Ask me anything about scheduling/i
      );
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(textarea, 'Test message');
      await user.click(sendButton);

      expect(mockSendMessage).toHaveBeenCalledTimes(1);
      expect(mockSendMessage).toHaveBeenCalledWith(
        'Test message',
        null,
        expect.any(Function)
      );
    });

    it('should clear input after sending', async () => {
      const user = userEvent.setup();
      render(<ClaudeCodeChat {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(
        /Ask me anything about scheduling/i
      ) as HTMLTextAreaElement;
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(textarea, 'Test message');
      await user.click(sendButton);

      expect(textarea.value).toBe('');
    });

    it('should not send empty message', async () => {
      const user = userEvent.setup();
      render(<ClaudeCodeChat {...defaultProps} />);

      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      expect(mockSendMessage).not.toHaveBeenCalled();
    });

    it('should not send whitespace-only message', async () => {
      const user = userEvent.setup();
      render(<ClaudeCodeChat {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(
        /Ask me anything about scheduling/i
      );
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(textarea, '   ');
      await user.click(sendButton);

      expect(mockSendMessage).not.toHaveBeenCalled();
    });

    it('should disable send button when input is empty', () => {
      render(<ClaudeCodeChat {...defaultProps} />);

      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).toBeDisabled();
    });

    it('should enable send button when input has text', async () => {
      const user = userEvent.setup();
      render(<ClaudeCodeChat {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(
        /Ask me anything about scheduling/i
      );
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(textarea, 'Test');

      expect(sendButton).not.toBeDisabled();
    });

    it('should send message on Ctrl+Enter', async () => {
      const user = userEvent.setup();
      render(<ClaudeCodeChat {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(
        /Ask me anything about scheduling/i
      );

      await user.type(textarea, 'Test message');
      await user.keyboard('{Control>}{Enter}{/Control}');

      expect(mockSendMessage).toHaveBeenCalledTimes(1);
    });
  });

  describe('Loading State', () => {
    it('should show processing status when loading', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages: [],
        isLoading: true,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('should disable input when loading', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages: [],
        isLoading: true,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(
        /Ask me anything about scheduling/i
      );
      expect(textarea).toBeDisabled();
    });

    it('should disable send button when loading', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages: [],
        isLoading: true,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      const sendButton = screen.getByRole('button', { name: /processing/i });
      expect(sendButton).toBeDisabled();
    });

    it('should show cancel button when loading', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages: [],
        isLoading: true,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should call cancelRequest when cancel button is clicked', async () => {
      const user = userEvent.setup();
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages: [],
        isLoading: true,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockCancelRequest).toHaveBeenCalledTimes(1);
    });
  });

  describe('Error State', () => {
    it('should show error status when error exists', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages: [],
        isLoading: false,
        error: 'Connection failed',
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('Error')).toBeInTheDocument();
    });
  });

  describe('Message Display', () => {
    it('should display user messages', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      const messages: ChatMessage[] = [
        {
          id: 'msg-1',
          role: 'user',
          content: 'Hello Claude',
          timestamp: new Date(),
        },
      ];

      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages,
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('Hello Claude')).toBeInTheDocument();
    });

    it('should display assistant messages', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      const messages: ChatMessage[] = [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'Hello! How can I help?',
          timestamp: new Date(),
        },
      ];

      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages,
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('Hello! How can I help?')).toBeInTheDocument();
    });

    it('should display user avatar for user messages', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      const messages: ChatMessage[] = [
        {
          id: 'msg-1',
          role: 'user',
          content: 'Test',
          timestamp: new Date(),
        },
      ];

      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages,
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('👤')).toBeInTheDocument();
    });

    it('should display bot avatar for assistant messages', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      const messages: ChatMessage[] = [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'Test',
          timestamp: new Date(),
        },
      ];

      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages,
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('🤖')).toBeInTheDocument();
    });

    it('should display streaming indicator for streaming messages', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      const messages: ChatMessage[] = [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'Partial response',
          timestamp: new Date(),
          isStreaming: true,
        },
      ];

      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages,
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('...')).toBeInTheDocument();
    });

    it('should display error in message when message has error', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      const messages: ChatMessage[] = [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'Failed',
          timestamp: new Date(),
          error: 'Request timeout',
        },
      ];

      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages,
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('Request timeout')).toBeInTheDocument();
    });

    it('should preserve line breaks in messages', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      const messages: ChatMessage[] = [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'Line 1\nLine 2\nLine 3',
          timestamp: new Date(),
        },
      ];

      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages,
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      const { container } = render(<ClaudeCodeChat {...defaultProps} />);

      // Check that <br /> tags were rendered
      const brTags = container.querySelectorAll('br');
      expect(brTags.length).toBeGreaterThan(0);
    });
  });

  describe('Code Blocks', () => {
    it('should display code blocks from messages', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      const messages: ChatMessage[] = [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'Here is some code',
          timestamp: new Date(),
          codeBlocks: [
            {
              language: 'python',
              code: 'print("Hello World")',
              filename: 'test.py',
            },
          ],
        },
      ];

      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages,
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('print("Hello World")')).toBeInTheDocument();
      expect(screen.getByText('python')).toBeInTheDocument();
      expect(screen.getByText('test.py')).toBeInTheDocument();
    });

    it('should display copy button for code blocks', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      const messages: ChatMessage[] = [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'Code',
          timestamp: new Date(),
          codeBlocks: [
            {
              language: 'python',
              code: 'print("test")',
            },
          ],
        },
      ];

      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages,
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('Copy')).toBeInTheDocument();
    });
  });

  describe('Artifacts', () => {
    it('should display artifact buttons when message has artifacts', () => {
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      const messages: ChatMessage[] = [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'Generated schedule',
          timestamp: new Date(),
          artifacts: [
            {
              id: 'art-1',
              type: 'schedule',
              title: 'Block 10 Schedule',
              data: {},
              createdAt: new Date(),
            },
          ],
        },
      ];

      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages,
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      expect(screen.getByText('Generated Artifacts:')).toBeInTheDocument();
      expect(screen.getByText(/Block 10 Schedule/i)).toBeInTheDocument();
    });
  });

  describe('Clear Messages', () => {
    it('should call clearMessages when clear button is clicked', async () => {
      const user = userEvent.setup();
      const mockUseContext = require('@/contexts/ClaudeChatContext').useClaudeChatContext;
      const messages: ChatMessage[] = [
        {
          id: 'msg-1',
          role: 'user',
          content: 'Test',
          timestamp: new Date(),
        },
      ];

      mockUseContext.mockReturnValue({
        session: { id: 'test-session' },
        messages,
        isLoading: false,
        error: null,
        initializeSession: mockInitializeSession,
        sendMessage: mockSendMessage,
        cancelRequest: mockCancelRequest,
        clearMessages: mockClearMessages,
        exportSession: jest.fn(),
        getSavedSessions: jest.fn(() => []),
        loadSession: jest.fn(),
      });

      render(<ClaudeCodeChat {...defaultProps} />);

      const clearButton = screen.getByRole('button', { name: /clear/i });
      await user.click(clearButton);

      expect(mockClearMessages).toHaveBeenCalledTimes(1);
    });

    it('should disable clear button when no messages', () => {
      render(<ClaudeCodeChat {...defaultProps} />);

      const clearButton = screen.getByRole('button', { name: /clear/i });
      expect(clearButton).toBeDisabled();
    });
  });

  describe('Task Completion Callback', () => {
    it('should call onTaskComplete when artifact is received', async () => {
      const mockOnTaskComplete = jest.fn();
      const user = userEvent.setup();

      // Mock sendMessage to call the stream update handler
      mockSendMessage.mockImplementation((query, context, onStreamUpdate) => {
        onStreamUpdate({
          type: 'artifact',
          content: '',
          metadata: { artifactId: 'test-artifact' },
        });
      });

      render(<ClaudeCodeChat {...defaultProps} onTaskComplete={mockOnTaskComplete} />);

      const textarea = screen.getByPlaceholderText(
        /Ask me anything about scheduling/i
      );
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(textarea, 'Generate schedule');
      await user.click(sendButton);

      expect(mockOnTaskComplete).toHaveBeenCalledWith({
        artifactId: 'test-artifact',
      });
    });
  });
});
