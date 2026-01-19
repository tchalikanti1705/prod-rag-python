/**
 * ChatMessage Component
 *
 * Displays a single message in the chat conversation.
 * Supports both user and assistant message styles.
 */

import type { ChatMessage as ChatMessageType } from '../types';

// =============================================================================
// Types
// =============================================================================

interface ChatMessageProps {
  message: ChatMessageType;
}

// =============================================================================
// Component
// =============================================================================

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`chat-message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-avatar">{isUser ? '👤' : '🤖'}</div>

      <div className="message-content">
        <div className="message-text">{message.content}</div>

        {/* Show sources for assistant messages */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="message-sources">
            <span className="sources-label">Sources:</span>
            <ul>
              {message.sources.map((source, index) => (
                <li key={index}>{source}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="message-timestamp">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
