import { useEffect } from 'react';
import { useDocStore } from '@/store/docStore';
import { DocumentItem } from './DocumentItem';
import { UploadZone } from './UploadZone';
import { Spinner } from '@/components/common/Spinner';
import { EmptyState } from '@/components/common/EmptyState';
import type { Document } from '@/types';

interface DocumentListProps {
  onSelect: (doc: Document) => void;
}

export function DocumentList({ onSelect }: DocumentListProps) {
  const { documents, isLoading, error, fetchDocuments, deleteDocument } = useDocStore();

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleSelect = (doc: Document) => {
    onSelect(doc);
  };

  const handleDelete = (id: string) => {
    deleteDocument(id);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-hearth-700">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wider">
          Documents
        </h2>
      </div>

      <UploadZone />

      <div className="flex-1 overflow-y-auto">
        {error && (
          <div className="px-4 py-3 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 mx-3 mt-2 rounded">
            {error}
            <button
              onClick={() => fetchDocuments()}
              className="ml-2 underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {isLoading && documents.length === 0 && (
          <div className="flex items-center justify-center py-12">
            <Spinner size="md" />
          </div>
        )}

        {!isLoading && !error && documents.length === 0 && (
          <EmptyState
            icon={<span className="text-3xl">{'\u{1F4C1}'}</span>}
            title="No documents yet"
            description="Upload a PDF, image, audio file, or text document to get started."
          />
        )}

        {documents.length > 0 && (
          <div className="py-1">
            {documents.map((doc) => (
              <DocumentItem
                key={doc.id}
                document={doc}
                onSelect={handleSelect}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
