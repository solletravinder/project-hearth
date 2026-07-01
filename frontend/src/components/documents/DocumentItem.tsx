import type { Document, DocType } from '@/types';
import { formatFileSize, formatDate } from '@/utils/format';

interface DocumentItemProps {
  document: Document;
  onSelect: (doc: Document) => void;
  onDelete: (id: string) => void;
}

const typeIcons: Record<DocType, string> = {
  pdf: '\u{1F4C4}',
  image: '\u{1F5BC}',
  audio: '\u{1F50A}',
  note: '\u{1F4DD}',
  text: '\u{1F4C4}',
};

const statusColors: Record<string, string> = {
  ready: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  processing: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

export function DocumentItem({ document, onSelect, onDelete }: DocumentItemProps) {
  const doc = document;

  return (
    <div
      className="flex items-start gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-hearth-800/50 cursor-pointer group transition-colors rounded-lg"
      onClick={() => onSelect(doc)}
    >
      <span className="text-lg shrink-0 mt-0.5" role="img" aria-label={doc.doc_type}>
        {typeIcons[doc.doc_type] || '\u{1F4C4}'}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
          {doc.title}
        </p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs text-gray-400 dark:text-gray-500">
            {formatFileSize(doc.file_size)}
          </span>
          <span className="text-xs text-gray-300 dark:text-gray-600">·</span>
          <span className="text-xs text-gray-400 dark:text-gray-500">
            {formatDate(doc.created_at)}
          </span>
          <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${statusColors[doc.status] || statusColors.pending}`}>
            {doc.status}
          </span>
        </div>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete(doc.id);
        }}
        className="p-1 rounded text-gray-300 hover:text-red-500 dark:hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
        title="Delete"
        aria-label="Delete document"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  );
}
