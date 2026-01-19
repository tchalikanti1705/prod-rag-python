/**
 * useFileUpload Hook
 *
 * Custom hook for managing PDF file uploads.
 * Handles file validation, upload state, and API communication.
 */

import { useState, useCallback } from 'react';
import type { LoadingState, IngestResponse } from '../types';
import { uploadPdf } from '../api/client';

// =============================================================================
// Types
// =============================================================================

interface UseFileUploadReturn {
  uploadState: LoadingState;
  uploadedFile: IngestResponse | null;
  error: string | null;
  uploadFile: (file: File) => Promise<void>;
  reset: () => void;
}

// =============================================================================
// Constants
// =============================================================================

const ALLOWED_TYPES = ['application/pdf'];
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

// =============================================================================
// Hook Implementation
// =============================================================================

export function useFileUpload(): UseFileUploadReturn {
  const [uploadState, setUploadState] = useState<LoadingState>('idle');
  const [uploadedFile, setUploadedFile] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  /**
   * Validate file before upload
   */
  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Only PDF files are allowed';
    }

    if (file.size > MAX_FILE_SIZE) {
      return 'File size must be less than 50MB';
    }

    return null;
  };

  /**
   * Upload a PDF file
   */
  const uploadFile = useCallback(async (file: File) => {
    // Reset state
    setError(null);
    setUploadedFile(null);

    // Validate file
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setUploadState('error');
      return;
    }

    setUploadState('loading');

    try {
      const response = await uploadPdf(file);
      setUploadedFile(response);
      setUploadState('success');
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to upload file';
      setError(errorMessage);
      setUploadState('error');
    }
  }, []);

  /**
   * Reset upload state
   */
  const reset = useCallback(() => {
    setUploadState('idle');
    setUploadedFile(null);
    setError(null);
  }, []);

  return {
    uploadState,
    uploadedFile,
    error,
    uploadFile,
    reset,
  };
}
