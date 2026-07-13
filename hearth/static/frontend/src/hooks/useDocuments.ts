import { useEffect } from 'react';
import { useDocStore } from '@/store/docStore';

export function useDocuments() {
  const store = useDocStore();

  useEffect(() => {
    store.fetchDocuments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return store;
}
