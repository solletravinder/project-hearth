import { useState, useEffect, useRef, useCallback } from 'react';
import { search as searchApi } from '@/api/client';

interface SearchResult {
  id: string;
  title: string;
  excerpt: string;
  score: number;
  document_id: string;
}

export function useSearch() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => {
    setIsOpen(false);
    setQuery('');
    setResults([]);
  }, []);

  const searchQuery = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([]);
      setIsLoading(false);
      return;
    }

    try {
      const res = await searchApi.query({ q, per_page: 10 });
      setResults(
        res.results.map((r) => ({
          id: r.chunk_id,
          title: r.doc_title,
          excerpt: r.content,
          score: r.score,
          document_id: r.document_id,
        })),
      );
    } catch {
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const search = useCallback((q: string) => {
    setQuery(q);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!q.trim()) {
      setResults([]);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    debounceRef.current = setTimeout(() => searchQuery(q), 300);
  }, [searchQuery]);

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return { results, query, isOpen, isLoading, open, close, search };
}
