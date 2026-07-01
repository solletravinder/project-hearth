import { create } from 'zustand';
import { apiClient } from '@/api/client';
import type { Document, UploadProgress } from '@/types';

interface DocState {
  documents: Document[];
  selectedDoc: Document | null;
  isLoading: boolean;
  error: string | null;
  uploadProgress: UploadProgress | null;
  isUploading: boolean;
  pollingInterval: number | null;
}

interface DocActions {
  fetchDocuments: (params?: { folder?: string; status?: string; doc_type?: string }) => Promise<void>;
  selectDocument: (doc: Document | null) => void;
  uploadFiles: (files: File[], folder?: string) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  batchDelete: (ids: string[]) => Promise<void>;
  reindexDocument: (id: string) => Promise<void>;
  startPolling: () => void;
  stopPolling: () => void;
}

type DocStore = DocState & DocActions;

export const useDocStore = create<DocStore>((set, get) => ({
  documents: [],
  selectedDoc: null,
  isLoading: false,
  error: null,
  uploadProgress: null,
  isUploading: false,
  pollingInterval: null,

  fetchDocuments: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const data = await apiClient.documents.list(params);
      set({ documents: data.items, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch documents',
        isLoading: false,
      });
    }
  },

  selectDocument: (doc) => set({ selectedDoc: doc }),

  uploadFiles: async (files, folder = 'default') => {
    set({
      isUploading: true,
      uploadProgress: { loaded: 0, total: files.reduce((a, f) => a + f.size, 0) },
    });
    try {
      for (const file of files) {
        await apiClient.documents.upload(file, folder);
      }
      set({ isUploading: false, uploadProgress: null });
      await get().fetchDocuments();
      get().startPolling();
    } catch (err) {
      set({
        isUploading: false,
        uploadProgress: null,
        error: err instanceof Error ? err.message : 'Upload failed',
      });
    }
  },

  deleteDocument: async (id) => {
    try {
      await apiClient.documents.delete(id);
      set((state) => ({
        documents: state.documents.filter((d) => d.id !== id),
        selectedDoc: state.selectedDoc?.id === id ? null : state.selectedDoc,
      }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Delete failed' });
    }
  },

  batchDelete: async (ids) => {
    try {
      await apiClient.documents.batchDelete(ids);
      set((state) => ({
        documents: state.documents.filter((d) => !ids.includes(d.id)),
        selectedDoc: state.selectedDoc && ids.includes(state.selectedDoc.id) ? null : state.selectedDoc,
      }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Batch delete failed' });
    }
  },

  reindexDocument: async (id) => {
    try {
      await apiClient.documents.reindex(id);
      await get().fetchDocuments();
      get().startPolling();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Reindex failed' });
    }
  },

  startPolling: () => {
    const existing = get().pollingInterval;
    if (existing) return;
    const interval = window.setInterval(async () => {
      await get().fetchDocuments();
      const { documents } = get();
      const hasProcessing = documents.some(
        (d) => d.status === 'pending' || d.status === 'processing',
      );
      if (!hasProcessing) {
        get().stopPolling();
      }
    }, 2000);
    set({ pollingInterval: interval });
  },

  stopPolling: () => {
    const { pollingInterval } = get();
    if (pollingInterval !== null) {
      clearInterval(pollingInterval);
      set({ pollingInterval: null });
    }
  },
}));

// Clean up polling on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    const { pollingInterval } = useDocStore.getState();
    if (pollingInterval !== null) clearInterval(pollingInterval);
  });
}
