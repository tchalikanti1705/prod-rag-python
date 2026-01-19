/**
 * API Client
 *
 * Centralized HTTP client for communicating with the FastAPI backend.
 * Follows single responsibility principle - only handles API communication.
 */

import type {
  QueryRequest,
  QueryResponse,
  IngestResponse,
  HealthResponse,
  DocumentsResponse,
} from '../types';

// =============================================================================
// Configuration
// =============================================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// =============================================================================
// Error Handling
// =============================================================================

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Handle API response and throw on error
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.detail || `HTTP error ${response.status}`,
      response.status,
      errorData
    );
  }
  return response.json();
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Check if the API server is healthy
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return handleResponse<HealthResponse>(response);
}

/**
 * Upload a PDF file for ingestion
 *
 * @param file - The PDF file to upload
 * @returns Promise with the ingestion response
 */
export async function uploadPdf(file: File): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  });

  return handleResponse<IngestResponse>(response);
}

/**
 * Query documents with a natural language question
 *
 * @param request - The query request with question and optional top_k
 * @returns Promise with the query response
 */
export async function queryDocuments(
  request: QueryRequest
): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse<QueryResponse>(response);
}

/**
 * List all uploaded documents
 *
 * @returns Promise with the list of documents
 */
export async function listDocuments(): Promise<DocumentsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/documents`);
  return handleResponse<DocumentsResponse>(response);
}
