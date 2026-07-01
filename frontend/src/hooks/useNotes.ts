import { useState, useEffect } from 'react';
import type { Note } from '@/types';

export function useNotes() {
  const [notes] = useState<Note[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Stub: will be connected when the notes API is ready
    setIsLoading(false);
  }, []);

  return { notes, isLoading };
}
