/**
 * ChatInput Component
 *
 * Input field for sending messages to the RAG system.
 * Handles form submission and loading states.
 */

import { useState, useCallback, useRef, useEffect } from 'react';

// =============================================================================
// Types
// =============================================================================

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

// =============================================================================
// Component
// =============================================================================

export function ChatInput({
  onSend,
  isLoading,
  placeholder = 'Ask a question about your documents...',
}: ChatInputProps) {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  /**
   * Focus input on mount
   */
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  /**
   * Handle form submission
   */
  const handleSubmit = useCallback(
    (event: React.FormEvent) => {
      event.preventDefault();

      const trimmedInput = input.trim();
      if (trimmedInput && !isLoading) {
        onSend(trimmedInput);
        setInput('');
      }
    },
    [input, isLoading, onSend]
  );

  /**
   * Handle keyboard shortcuts
   */
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      // Submit on Enter (without Shift)
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSubmit(event);
      }
    },
    [handleSubmit]
  );

  /**
   * Auto-resize textarea
   */
  const handleInput = useCallback(
    (event: React.ChangeEvent<HTMLTextAreaElement>) => {
      const textarea = event.target;
      setInput(textarea.value);

      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    },
    []
  );

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <textarea
        ref={inputRef}
        value={input}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isLoading}
        rows={1}
        aria-label="Message input"
      />

      <button
        type="submit"
        disabled={!input.trim() || isLoading}
        aria-label="Send message"
      >
        {isLoading ? (
          <span className="spinner-small" />
        ) : (
          <span>Send</span>
        )}
      </button>
    </form>
  );
}
