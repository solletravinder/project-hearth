import { useRef, useEffect } from 'react';
import { useSearch } from '@/hooks/useSearch';
import { SearchResults } from './SearchResults';
import { DebouncedInput } from '@/components/common/DebouncedInput';

interface SearchDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SearchDialog({ isOpen, onClose }: SearchDialogProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const { results, query, search, close, isLoading } = useSearch();

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        close();
        onClose();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, close, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => {
          close();
          onClose();
        }}
      />

      {/* Dialog */}
      <div className="relative z-10 w-full max-w-lg mx-4 rounded-xl bg-white dark:bg-hearth-800 shadow-2xl border border-gray-200 dark:border-hearth-700 overflow-hidden">
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-hearth-700">
          <svg className="w-5 h-5 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <DebouncedInput
            ref={inputRef}
            value={query}
            onChange={search}
            delay={300}
            placeholder="Search documents, notes, conversations..."
            className="flex-1 bg-transparent border-none outline-none text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
            ariaLabel="Search"
          />
          <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-xs font-mono text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-hearth-700">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-64 overflow-y-auto p-2">
          <SearchResults query={query} results={results} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
}
