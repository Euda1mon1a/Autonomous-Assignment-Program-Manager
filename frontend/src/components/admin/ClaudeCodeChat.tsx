import React, { useEffect, useRef, useState } from 'react';
import { useClaudeChatContext } from '../../contexts/ClaudeChatContext';
import { ChatMessage, StreamUpdate, ChatArtifact, ClaudeCodeExecutionContext } from '../../types/chat';
import './ClaudeCodeChat.css';

interface ClaudeCodeChatProps {
  programId: string;
  adminId: string;
  onTaskComplete?: (artifact: ChatArtifact) => void;
}

const ClaudeCodeChat: React.FC<ClaudeCodeChatProps> = ({
  programId,
  adminId,
  onTaskComplete,
}) => {
  const {
    session,
    messages,
    isLoading,
    error,
    initializeSession,
    sendMessage,
    cancelRequest,
    clearMessages,
  } = useClaudeChatContext();

  const [input, setInput] = useState('');
  const [context, setContext] = useState<Partial<ClaudeCodeExecutionContext> | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<ChatArtifact | null>(null);

  // Initialize session on mount
  useEffect(() => {
    if (!session) {
      initializeSession(programId, adminId, 'Schedule Assistant');
    }
  }, [programId, adminId, session, initializeSession]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuery = input;
    setInput('');

    const handleStreamUpdate = (update: StreamUpdate) => {
      // Handle real-time stream updates
      if (update.type === 'artifact') {
        onTaskComplete?.(update.metadata);
      }
    };

    await sendMessage(userQuery, context, handleStreamUpdate);
  };

  const handleCancelRequest = () => {
    cancelRequest();
  };

  const formatContent = (content: string) => {
    return content.split('\n').map((line, i) => (
      <React.Fragment key={i}>
        {line}
        <br />
      </React.Fragment>
    ));
  };

  const renderCodeBlock = (code: { language: string; code: string; filename?: string }, index: number): React.ReactElement => (
    <div key={index} className="code-block">
      <div className="code-header">
        <span className="language">{code.language}</span>
        {code.filename && <span className="filename">{code.filename}</span>}
        <button
          className="copy-button"
          onClick={() => {
            navigator.clipboard.writeText(code.code);
          }}
          title="Copy code"
        >
          Copy
        </button>
      </div>
      <pre>
        <code>{code.code}</code>
      </pre>
    </div>
  );

  const renderMessage = (msg: ChatMessage) => (
    <div key={msg.id} className={`message message-${msg.role}`}>
      <div className="message-avatar">
        {msg.role === 'user' ? '👤' : '🤖'}
      </div>
      <div className="message-content">
        <div className="message-text">{formatContent(msg.content)}</div>

        {msg.codeBlocks && msg.codeBlocks.length > 0 && (
          <div className="code-blocks">
            {msg.codeBlocks.map((code, i) => renderCodeBlock(code, i))}
          </div>
        )}

        {msg.artifacts && msg.artifacts.length > 0 && (
          <div className="artifacts-container">
            <div className="artifacts-header">Generated Artifacts:</div>
            {msg.artifacts.map((artifact, i) => (
              <button
                key={i}
                className="artifact-button"
                onClick={() => setSelectedArtifact(artifact)}
              >
                📊 {artifact.title}
              </button>
            ))}
          </div>
        )}

        {msg.error && <div className="message-error">{msg.error}</div>}
        {msg.isStreaming && <div className="streaming-indicator">...</div>}
      </div>
    </div>
  );

  return (
    <div className="claude-code-chat">
      <div className="chat-header">
        <h3>Claude Code Assistant</h3>
        <div className="chat-status">
          {isLoading && (
            <span className="status-badge loading">Processing...</span>
          )}
          {error && <span className="status-badge error">Error</span>}
          {!isLoading && !error && (
            <span className="status-badge ready">Ready</span>
          )}
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">💬</div>
            <h4>Start a conversation</h4>
            <p>
              Ask me to help with schedule generation, compliance analysis, or
              any scheduling tasks.
            </p>
            <div className="quick-prompts">
              <button
                className="quick-prompt"
                onClick={() =>
                  setInput(
                    'Generate the schedule for the next rotation block'
                  )
                }
              >
                Generate Schedule
              </button>
              <button
                className="quick-prompt"
                onClick={() =>
                  setInput('Analyze compliance violations for all residents')
                }
              >
                Check Compliance
              </button>
              <button
                className="quick-prompt"
                onClick={() =>
                  setInput('Export a detailed analysis report')
                }
              >
                Export Report
              </button>
            </div>
          </div>
        ) : (
          messages.map(renderMessage)
        )}
        <div ref={messagesEndRef} />
      </div>

      {selectedArtifact && (
        <div className="artifact-viewer">
          <div className="artifact-header">
            <h4>{selectedArtifact.title}</h4>
            <button
              className="close-button"
              onClick={() => setSelectedArtifact(null)}
            >
              ✕
            </button>
          </div>
          <div className="artifact-content">
            <pre>{JSON.stringify(selectedArtifact.data, null, 2)}</pre>
          </div>
          <div className="artifact-actions">
            <button
              className="action-button primary"
              onClick={() => {
                // Handle artifact acceptance
                setSelectedArtifact(null);
              }}
            >
              Apply Changes
            </button>
            <button
              className="action-button secondary"
              onClick={() => {
                // Download artifact
                const dataStr = JSON.stringify(
                  selectedArtifact.data,
                  null,
                  2
                );
                const dataBlob = new Blob([dataStr], {
                  type: 'application/json',
                });
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `${selectedArtifact.title}.json`;
                link.click();
              }}
            >
              Download
            </button>
          </div>
        </div>
      )}

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <div className="input-wrapper">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about scheduling, compliance, or reports..."
            disabled={isLoading}
            rows={3}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.ctrlKey) {
                handleSendMessage(e as any);
              }
            }}
          />
          <div className="input-actions">
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="send-button"
            >
              {isLoading ? '⏳ Processing' : '➤ Send'}
            </button>
            {isLoading && (
              <button
                type="button"
                onClick={handleCancelRequest}
                className="cancel-button"
              >
                Cancel
              </button>
            )}
            <button
              type="button"
              onClick={clearMessages}
              className="clear-button"
              disabled={messages.length === 0}
            >
              Clear
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default ClaudeCodeChat;
