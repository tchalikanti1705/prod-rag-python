/**
 * ChatInput Component
 *
 * Input field for sending messages to the RAG system.
 * Handles form submission, loading states, and speech-to-text.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';

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
  
  // Speech recognition
  const {
    isSupported: isSpeechSupported,
    status: speechStatus,
    transcript,
    interimTranscript,
    error: speechError,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechRecognition();

  const isListening = speechStatus === 'listening';

  /**
   * Update input when speech transcript changes
   */
  useEffect(() => {
    if (transcript) {
      setInput(prev => {
        // If previous input ends with space or is empty, just append
        if (!prev || prev.endsWith(' ')) {
          return prev + transcript;
        }
        return prev + ' ' + transcript;
      });
      resetTranscript();
    }
  }, [transcript, resetTranscript]);

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

  /**
   * Toggle speech recognition
   */
  const handleMicClick = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  // Combine input with interim transcript for display
  const displayValue = isListening && interimTranscript 
    ? input + (input && !input.endsWith(' ') ? ' ' : '') + interimTranscript
    : input;

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      {/* Speech error tooltip */}
      {speechError && (
        <div className="speech-error-tooltip">
          {speechError}
        </div>
      )}
      
      <div className="input-wrapper">
        <textarea
          ref={inputRef}
          value={displayValue}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={isListening ? 'Listening...' : placeholder}
          disabled={isLoading}
          rows={1}
          aria-label="Message input"
          className={isListening ? 'listening' : ''}
        />
        
        {/* Microphone button */}
        {isSpeechSupported && (
          <button
            type="button"
            className={`mic-button ${isListening ? 'listening' : ''}`}
            onClick={handleMicClick}
            disabled={isLoading}
            aria-label={isListening ? 'Stop listening' : 'Start voice input'}
            title={isListening ? 'Stop listening' : 'Voice input'}
          >
            {isListening ? (
              <span className="mic-icon listening">
                <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                  <rect x="4" y="4" width="6" height="16" rx="1" />
                  <rect x="14" y="4" width="6" height="16" rx="1" />
                </svg>
              </span>
            ) : (
              <span className="mic-icon">
                <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
              </span>
            )}
          </button>
        )}
      </div>

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
