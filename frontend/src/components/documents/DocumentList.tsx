import { useDocuments } from '@/hooks/useDocuments';
import { DocumentItem } from './DocumentItem';
import { UploadZone } from './UploadZone';
import { EmptyState } from '@/components/common/EmptyState';
import { Spinner } from '@/components/common/Spinner';
import type { Document } from '@/types';

interface DocumentListProps {
  onSelect: (doc: Document) => void;
}

export function DocumentList({ onSelect }: DocumentListProps) {
  const { documents, isLoading, error, deleteDocument, uploadFiles, isUploading } = useDocuments();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-4 py-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3 text-sm text-red-700 dark:text-red-400">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {documents.length === 0 ? (
          <EmptyState
            title="No documents yet"
            description="Upload PDFs, images, or text files to get started."
          />
        ) : (
          documents.map((doc) => (
            <DocumentItem
              key={doc.id}
              document={doc}
              onSelect={onSelect}
              onDelete={deleteDocument}
            />
          ))
        )}
      </div>
      <UploadZone
        onUpload={uploadFiles}
        isUploading={isUploading}
      />
    </div>
  );
}
