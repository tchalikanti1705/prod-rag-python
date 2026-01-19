/**
 * DocumentList Component
 *
 * Displays a list of uploaded documents.
 * Shows document count and names.
 */

import { useEffect, useState } from 'react';
import { listDocuments } from '../api/client';
import type { DocumentsResponse } from '../types';

// =============================================================================
// Component
// =============================================================================

export function DocumentList() {
  const [documents, setDocuments] = useState<DocumentsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch documents on mount
   */
  useEffect(() => {
    async function fetchDocuments() {
      try {
        const response = await listDocuments();
        setDocuments(response);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load documents');
      } finally {
        setIsLoading(false);
      }
    }

    fetchDocuments();
  }, []);

  /**
   * Refresh documents list
   */
  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      const response = await listDocuments();
      setDocuments(response);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="document-list">
        <div className="loading">Loading documents...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="document-list">
        <div className="error">{error}</div>
        <button onClick={handleRefresh}>Retry</button>
      </div>
    );
  }

  return (
    <div className="document-list">
      <div className="document-header">
        <h3>📚 Documents ({documents?.count || 0})</h3>
        <button onClick={handleRefresh} className="refresh-btn" title="Refresh">
          🔄
        </button>
      </div>

      {documents && documents.documents.length > 0 ? (
        <ul>
          {documents.documents.map((doc, index) => (
            <li key={index}>
              <span className="doc-icon">📄</span>
              <span className="doc-name">{doc}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="no-documents">No documents uploaded yet</p>
      )}
    </div>
  );
}
