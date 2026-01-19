/**
 * useChat Hook
 *
 * Custom hook for managing chat state and interactions.
 * Encapsulates all chat-related logic following the single responsibility principle.
 */

import { useState, useCallback } from 'react';
import type { ChatMessage, LoadingState } from '../types';
import { queryDocuments } from '../api/client';

// =============================================================================
// Types
// =============================================================================

interface UseChatReturn {
  messages: ChatMessage[];
  loadingState: LoadingState;
  error: string | null;
  sendMessage: (question: string, topK?: number) => Promise<void>;
  clearMessages: () => void;
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Generate a unique ID for messages
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [error, setError] = useState<string | null>(null);

  /**
   * Send a message and get AI response
   */
  const sendMessage = useCallback(async (question: string, topK = 5) => {
    // Clear previous errors
    setError(null);

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: question,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoadingState('loading');

    try {
      // Query the API
      const response = await queryDocuments({ question, top_k: topK });

      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setLoadingState('success');
    } catch (err) {
      let errorMessage =
        err instanceof Error ? err.message : 'Failed to get response';
      
      // Provide helpful message for common errors
      if (errorMessage.includes('500') || errorMessage.includes('Internal Server Error')) {
        errorMessage = 'Please upload a PDF document first before asking questions.';
      }
      
      setError(errorMessage);
      setLoadingState('error');

      // Add error message as assistant response
      const errorAssistantMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorAssistantMessage]);
    }
  }, []);

  /**
   * Clear all messages
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    setLoadingState('idle');
  }, []);

  return {
    messages,
    loadingState,
    error,
    sendMessage,
    clearMessages,
  };
}
