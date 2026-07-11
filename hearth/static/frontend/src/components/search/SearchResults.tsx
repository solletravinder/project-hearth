import { EmptyState } from '@/components/common/EmptyState';

interface SearchResult {
  id: string;
  title: string;
  excerpt: string;
  score: number;
}

interface SearchResultsProps {
  query: string;
  results: SearchResult[];
  isLoading?: boolean;
  onSelect?: (result: SearchResult) => void;
}

export function SearchResults({ query, results, isLoading, onSelect }: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="py-8 text-center text-sm text-gray-400 dark:text-gray-500">
        Searching...
      </div>
    );
  }

  if (query && results.length === 0) {
    return (
      <EmptyState
        title="No results"
        description={`No results found for "${query}".`}
      />
    );
  }

  if (!query) {
    return (
      <div className="py-8 text-center text-sm text-gray-400 dark:text-gray-500">
        Type to search across documents, notes, and conversations.
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {results.map((result) => (
        <div
          key={result.id}
          className="px-3 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-hearth-700 cursor-pointer"
          onClick={() => onSelect?.(result)}
        >
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {result.title}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">
            {result.excerpt}
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
            Score: {(result.score * 100).toFixed(0)}%
          </p>
        </div>
      ))}
    </div>
  );
}
