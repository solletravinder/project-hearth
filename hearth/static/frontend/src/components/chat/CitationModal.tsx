import type { Citation } from '@/types';

interface CitationModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export function CitationModal({ citation, onClose }: CitationModalProps) {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg bg-white dark:bg-hearth-800 border border-gray-200 dark:border-hearth-700 rounded-xl shadow-2xl overflow-hidden max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-hearth-750 bg-gray-50 dark:bg-hearth-900/50">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate pr-4 text-sm">
            Source Context: {citation.doc_title}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors text-sm"
          >
            &#10005;
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          <div className="flex items-center space-x-3 text-xs">
            <span className={`px-2 py-0.5 rounded-full border font-medium ${
              citation.color === 'green'
                ? 'bg-green-50 text-green-700 border-green-200 dark:bg-green-950/20 dark:text-green-400 dark:border-green-800'
                : 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-800'
            }`}>
              {citation.verified ? '✓ Verified Claim' : '⚠ Unverified Claim'}
            </span>
            <span className="text-gray-500 dark:text-gray-400 font-medium">
              Score: {(citation.score * 100).toFixed(0)}%
            </span>
          </div>

          <div className="p-3 bg-gray-50 dark:bg-hearth-900/30 border border-gray-100 dark:border-hearth-750 rounded-lg text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed select-text">
            {citation.text}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end px-4 py-3 border-t border-gray-100 dark:border-hearth-750 bg-gray-50 dark:bg-hearth-900/50">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-white bg-hearth-650 hover:bg-hearth-700 rounded transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
