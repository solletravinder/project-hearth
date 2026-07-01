import { useState } from 'react';

interface SearchResult {
  id: string;
  title: string;
  excerpt: string;
  score: number;
}

export function useSearch() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const open = () => setIsOpen(true);
  const close = () => {
    setIsOpen(false);
    setQuery('');
    setResults([]);
  };

  const search = async (q: string) => {
    setQuery(q);
    if (!q.trim()) {
      setResults([]);
      return;
    }
    // Stub: will be connected when search API is ready
    setResults([]);
  };

  return { results, query, isOpen, open, close, search };
}
