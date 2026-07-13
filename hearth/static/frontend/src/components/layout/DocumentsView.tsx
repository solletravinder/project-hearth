import { useState } from 'react';
import { DocumentList } from '../documents/DocumentList';
import { DocumentPreview } from '../documents/DocumentPreview';
import type { Document } from '@/types';

interface DocumentsViewProps {
  onSelect?: (doc: Document) => void;
}

export function DocumentsView({ onSelect }: DocumentsViewProps) {
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);

  const handleSelect = (doc: Document) => {
    setSelectedDoc(doc);
    if (onSelect) onSelect(doc);
  };

  return (
    <div className="flex flex-col h-full">
      <DocumentList onSelect={handleSelect} />
      {selectedDoc && <DocumentPreview documentId={selectedDoc.id} />}
    </div>
  );
}