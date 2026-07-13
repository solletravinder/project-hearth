import { useEffect, useState } from 'react';
import { apiClient } from '@/api/client';
import type { Document } from '@/types';

interface DocumentPreviewProps {
  documentId?: string;
}

export function DocumentPreview({ documentId }: DocumentPreviewProps) {
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!documentId) return;

    const fetchDocument = async () => {
      setLoading(true);
      setError(null);
      try {
        const doc = await apiClient.documents.get(documentId);
        setDocument(doc);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load document');
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
  }, [documentId]);

  if (!documentId) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-gray-400 dark:text-gray-500">
        Select a document to preview
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400 dark:text-gray-500">Loading document...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-500 dark:text-red-400">
        Error: {error}
      </div>
    );
  }

  if (!document) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-gray-400 dark:text-gray-500">
        Document not found
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="flex-1 flex flex-col">
      <div className="p-4 border-b border-gray-200 dark:border-hearth-700">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {document.title}
            </h2>
            <div className="flex items-center gap-4 mt-1 text-xs text-gray-500 dark:text-gray-400">
              <span>Type: {document.doc_type}</span>
              <span>Size: {formatFileSize(document.file_size)}</span>
              <span>Status: {document.status}</span>
            </div>
            <div className="flex items-center gap-4 mt-1 text-xs text-gray-400 dark:text-gray-500">
              <span>Created: {formatDate(document.created_at)}</span>
              <span>Chunks: {document.chunk_count}</span>
            </div>
          </div>
          <a
            href={apiClient.documents.download(document.id)}
            download
            className="px-3 py-1 text-xs text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
          >
            Download
          </a>
        </div>
      </div>

      <div className="flex-1 p-4 overflow-y-auto">
        {document.error_message && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded">
            Error: {document.error_message}
          </div>
        )}

        <div className="bg-gray-50 dark:bg-hearth-800 rounded-lg p-4">
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            Document Content Preview
          </div>
          <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {document.doc_type === 'text'
              ? `This is a preview of the text document "${document.title}".\n\nIn a production environment, the actual file content would be displayed here.`
              : document.doc_type === 'pdf'
              ? `PDF Document: ${document.title}\nPages: ${document.page_count ?? 'Unknown'}`
              : document.doc_type === 'image'
              ? `Image Document: ${document.title}`
              : document.doc_type === 'audio'
              ? `Audio Document: ${document.title}`
              : `Document type: ${document.doc_type}`}
          </pre>
        </div>
      </div>
    </div>
  );
}