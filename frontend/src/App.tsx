/**
 * App Component
 *
 * Root component for the RAG application.
 * Provides the main layout with sidebar for uploads and main area for chat.
 */

import { useRef, useEffect } from 'react';
import { FileUpload, ChatMessage, ChatInput, DocumentList } from './components';
import { useChat, useFileUpload } from './hooks';
import './App.css';

// =============================================================================
// Component
// =============================================================================

function App() {
  const { messages, loadingState, sendMessage, clearMessages } = useChat();
  const { uploadState, uploadedFile, error: uploadError, uploadFile, reset: resetUpload } = useFileUpload();
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  /**
   * Scroll to bottom when new messages arrive
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Handle file upload
   */
  const handleUpload = (file: File) => {
    uploadFile(file);
  };

  /**
   * Handle message send
   */
  const handleSend = (message: string) => {
    sendMessage(message);
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>📚 RAG Chat</h1>
          <p className="subtitle">Upload PDFs and ask questions</p>
        </div>

        <div className="sidebar-section">
          <h2>Upload PDF</h2>
          <FileUpload
            onUpload={handleUpload}
            uploadState={uploadState}
            error={uploadError}
            successMessage={uploadedFile?.message}
          />
          {uploadState === 'success' && (
            <button className="reset-btn" onClick={resetUpload}>
              Upload Another
            </button>
          )}
        </div>

        <div className="sidebar-section">
          <DocumentList />
        </div>

        <div className="sidebar-footer">
          <button className="clear-btn" onClick={clearMessages}>
            🗑️ Clear Chat
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="chat-container">
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">💬</div>
              <h2>Start a Conversation</h2>
              <p>Upload a PDF document and ask questions about its content.</p>
              <p className="hint">The AI will use the document context to answer your questions.</p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {/* Loading indicator while waiting for AI response */}
              {loadingState === 'loading' && (
                <div className="chat-message assistant">
                  <div className="message-avatar">🤖</div>
                  <div className="message-content loading-message">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <div className="loading-text">AI is thinking...</div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <ChatInput
          onSend={handleSend}
          isLoading={loadingState === 'loading'}
        />
      </main>
    </div>
  );
}

export default App;
