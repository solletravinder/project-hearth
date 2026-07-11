import { useState, useEffect } from 'react';
import type { Note } from '@/types';
import { apiClient } from '@/api/client';


export function useNotes() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNotes = async () => {
      try {
        const response = await apiClient.notes.list();
        setNotes(response.notes);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch notes');
      } finally {
        setIsLoading(false);
      }
    };

    fetchNotes();
  }, []);

  return { notes, isLoading, error };
}