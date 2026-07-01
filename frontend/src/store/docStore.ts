import { create } from 'zustand';
import type { Document } from '@/types';
import { documents as documentsApi } from '@/api/client';

interface DocState {
  documents: Document[];
  selectedDoc: Document | null;
  uploadProgress: number;
  isUploading: boolean;
  isLoading: boolean;
  error: string | null;
}

interface DocActions {
  fetchDocuments: (folder?: string) => Promise<void>;
  uploadFiles: (files: FileList | File[], folder?: string) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  reindexDocument: (id: string) => Promise<void>;
  selectDocument: (doc: Document | null) => void;
}

type DocStore = DocState & DocActions;

export const useDocStore = create<DocStore>((set, get) => ({
  documents: [],
  selectedDoc: null,
  uploadProgress: 0,
  isUploading: false,
  isLoading: false,
  error: null,

  fetchDocuments: async (folder?: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await documentsApi.list({ folder });
      set({ documents: res.documents, isLoading: false, error: null });
    } catch {
      set({ isLoading: false, error: 'Failed to load documents' });
    }
  },

  uploadFiles: async (files: FileList | File[], folder?: string) => {
    set({ isUploading: true, uploadProgress: 0, error: null });
    const fileArr = Array.from(files);
    let uploaded = 0;

    try {
      for (const file of fileArr) {
        await documentsApi.upload(file, folder);
        uploaded++;
        set({ uploadProgress: Math.round((uploaded / fileArr.length) * 100) });
      }
      set({ isUploading: false, uploadProgress: 100 });
      await get().fetchDocuments(folder);
    } catch {
      set({ isUploading: false, error: 'Upload failed' });
    }
  },

  deleteDocument: async (id: string) => {
    try {
      await documentsApi.delete(id);
      set((s) => ({
        documents: s.documents.filter((d) => d.id !== id),
        selectedDoc: s.selectedDoc?.id === id ? null : s.selectedDoc,
        error: null,
      }));
    } catch {
      set({ error: 'Failed to delete document' });
    }
  },

  reindexDocument: async (id: string) => {
    try {
      const updated = await documentsApi.reindex(id);
      set((s) => ({
        documents: s.documents.map((d) => (d.id === id ? updated : d)),
        error: null,
      }));
    } catch {
      set({ error: 'Failed to reindex document' });
    }
  },

  selectDocument: (doc: Document | null) => {
    set({ selectedDoc: doc });
  },
}));
