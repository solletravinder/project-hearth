interface DocumentPreviewProps {
  documentId?: string;
}

export function DocumentPreview({ documentId }: DocumentPreviewProps) {
  if (!documentId) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-gray-400 dark:text-gray-500">
        Select a document to preview
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center h-full text-sm text-gray-400 dark:text-gray-500">
      Preview coming soon
    </div>
  );
}
