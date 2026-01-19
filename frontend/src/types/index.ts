/**
 * Type Definitions
 *
 * Centralized type definitions for the RAG application.
 * These types mirror the backend Pydantic models for type safety.
 */

// =============================================================================
// API Response Types
// =============================================================================

/**
 * Response from the query endpoint
 */
export interface QueryResponse {
  answer: string;
  sources: string[];
  num_contexts: number;
}

/**
 * Response from the upload endpoint
 */
export interface IngestResponse {
  message: string;
  filename: string;
  event_id: string;
}

/**
 * Response from the health check endpoint
 */
export interface HealthResponse {
  status: string;
  message: string;
}

/**
 * Response from the documents list endpoint
 */
export interface DocumentsResponse {
  documents: string[];
  count: number;
}

// =============================================================================
// API Request Types
// =============================================================================

/**
 * Request payload for querying documents
 */
export interface QueryRequest {
  question: string;
  top_k?: number;
}

// =============================================================================
// UI State Types
// =============================================================================

/**
 * Loading states for async operations
 */
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * Chat message in the conversation
 */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp: Date;
}
