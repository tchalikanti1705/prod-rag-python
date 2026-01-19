/**
 * FileUpload Component
 *
 * A drag-and-drop file upload component for PDF documents.
 * Supports both drag-and-drop and click-to-browse functionality.
 */

import { useCallback, useRef, useState } from 'react';
import type { LoadingState } from '../types';

// =============================================================================
// Types
// =============================================================================

interface FileUploadProps {
  onUpload: (file: File) => void;
  uploadState: LoadingState;
  error: string | null;
  successMessage?: string;
}

// =============================================================================
// Component
// =============================================================================

export function FileUpload({
  onUpload,
  uploadState,
  error,
  successMessage,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  /**
   * Handle file selection from input
   */
  const handleFileChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
        onUpload(file);
      }
    },
    [onUpload]
  );

  /**
   * Handle drag events
   */
  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      setIsDragging(false);

      const file = event.dataTransfer.files[0];
      if (file) {
        onUpload(file);
      }
    },
    [onUpload]
  );

  /**
   * Trigger file input click
   */
  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  // Determine status styling
  const isLoading = uploadState === 'loading';
  const isSuccess = uploadState === 'success';
  const isError = uploadState === 'error';

  return (
    <div className="file-upload">
      <div
        className={`upload-zone ${isDragging ? 'dragging' : ''} ${isSuccess ? 'success' : ''} ${isError ? 'error' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-label="Upload PDF file"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          hidden
        />

        {isLoading ? (
          <div className="upload-loading">
            <div className="spinner" />
            <p>Uploading...</p>
          </div>
        ) : isSuccess ? (
          <div className="upload-success">
            <span className="icon">✓</span>
            <p>{successMessage || 'Upload successful!'}</p>
          </div>
        ) : (
          <div className="upload-prompt">
            <span className="icon">📄</span>
            <p>Drag & drop a PDF here</p>
            <p className="subtext">or click to browse</p>
          </div>
        )}
      </div>

      {error && <p className="upload-error">{error}</p>}
    </div>
  );
}
