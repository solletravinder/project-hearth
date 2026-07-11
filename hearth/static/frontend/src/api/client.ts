import type {
  Document,
  Conversation,
  Message,
  Note,
  AppSettings,
  ChatRequest,
  ChatResponse,
} from '@/types';

/* ── Helpers ─────────────────────────────────────────────────── */

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: options?.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new ApiError(res.status, body || `Request failed (${res.status})`);
  }

  return res.json() as Promise<T>;
}

/* ── Documents API ───────────────────────────────────────────── */

interface ListDocsParams {
  folder?: string;
  doc_type?: string;
  status?: string;
  page?: number;
  per_page?: number;
}

interface ListDocsResponse {
  items: Document[];
  page: number;
  per_page: number;
}

export const documents = {
  list(params?: ListDocsParams): Promise<ListDocsResponse> {
    const qs = new URLSearchParams();
    if (params?.folder) qs.set('folder', params.folder);
    if (params?.doc_type) qs.set('doc_type', params.doc_type);
    if (params?.status) qs.set('status', params.status);
    if (params?.page) qs.set('page', String(params.page));
    if (params?.per_page) qs.set('per_page', String(params.per_page));
    const query = qs.toString();
    return request(query ? `/documents?${query}` : '/documents');
  },

  get(id: string): Promise<Document> {
    return request(`/documents/${id}`);
  },

  upload(file: File, folder?: string): Promise<Document> {
    const form = new FormData();
    form.append('file', file);
    if (folder) form.append('folder', folder);
    return request('/documents/upload', {
      method: 'POST',
      body: form,
    });
  },

  delete(id: string): Promise<void> {
    return request(`/documents/${id}`, { method: 'DELETE' });
  },

  batchDelete(ids: string[]): Promise<void> {
    return request('/documents/batch-delete', {
      method: 'POST',
      body: JSON.stringify({ ids }),
    });
  },

  download(id: string): string {
    return `/api/documents/${id}/download`;
  },

  reindex(id: string): Promise<Document> {
    return request(`/documents/${id}/reindex`, { method: 'POST' });
  },
};

/* ── Search API ─────────────────────────────────────────────── */

interface SearchParams {
  q: string;
  doc_type?: string;
  folder?: string;
  page?: number;
  per_page?: number;
}

interface SearchResponse {
  items: Document[];
  total: number;
  page: number;
  per_page: number;
  query: string;
}

export const search = {
  query(params: SearchParams): Promise<SearchResponse> {
    const qs = new URLSearchParams();
    qs.set('q', params.q);
    if (params.doc_type) qs.set('doc_type', params.doc_type);
    if (params.folder) qs.set('folder', params.folder);
    if (params.page) qs.set('page', String(params.page));
    if (params.per_page) qs.set('per_page', String(params.per_page));
    return request(`/search/?${qs.toString()}`);
  },
};

/* ── Conversations API ───────────────────────────────────────── */

export const conversations = {
  list(page = 1): Promise<{ conversations: Conversation[]; total: number }> {
    return request(`/conversations?page=${page}`);
  },

  create(title?: string): Promise<Conversation> {
    return request('/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  },

  delete(id: string): Promise<void> {
    return request(`/conversations/${id}`, { method: 'DELETE' });
  },

  messages(id: string, page = 1): Promise<{ messages: Message[]; total: number }> {
    return request(`/conversations/${id}/messages?page=${page}`);
  },
};

/* ── Chat API ────────────────────────────────────────────────── */

export const chat = {
  send(req: ChatRequest): Promise<ChatResponse> {
    return request('/chat', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },
};

/* ── Notes API ───────────────────────────────────────────────── */

interface ListNotesParams {
  page?: number;
  per_page?: number;
  tag?: string;
}

export const notes = {
  list(params?: ListNotesParams): Promise<{ notes: Note[]; total: number }> {
    const qs = new URLSearchParams();
    if (params?.page) qs.set('page', String(params.page));
    if (params?.per_page) qs.set('per_page', String(params.per_page));
    if (params?.tag) qs.set('tag', params.tag);
    const query = qs.toString();
    return request(query ? `/notes?${query}` : '/notes');
  },

  create(data: { title: string; content: string; tags?: string[] }): Promise<Note> {
    return request('/notes', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  get(id: string): Promise<Note> {
    return request(`/notes/${id}`);
  },

  update(id: string, data: Partial<{ title: string; content: string; tags: string[] }>): Promise<Note> {
    return request(`/notes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete(id: string): Promise<void> {
    return request(`/notes/${id}`, { method: 'DELETE' });
  },
};

/* ── Settings API ────────────────────────────────────────────── */

export const settings = {
  async get(): Promise<AppSettings> {
    const res = await request<{ settings: AppSettings }>('/settings');
    return res.settings;
  },

  async update(data: Partial<AppSettings>): Promise<AppSettings> {
    const res = await request<{ settings: AppSettings }>('/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    return res.settings;
  },
};

/* ── Models API ──────────────────────────────────────────────── */

interface ModelEntryInfo {
  status: string;
  loaded_at: string | null;
  memory_mb: number;
  error: string | null;
}

interface ModelStatusResponse {
  models: {
    models: Record<string, ModelEntryInfo>;
    active_profile: string | null;
    loaded_count: number;
  };
  providers: Record<string, unknown>;
  active_profile: string;
}

export const models = {
  status(): Promise<ModelStatusResponse> {
    return request('/models/status');
  },

  profiles(): Promise<{ profiles: string[] }> {
    return request('/models/profiles');
  },

  unload(name: string): Promise<void> {
    return request(`/models/${encodeURIComponent(name)}/unload`, { method: 'POST' });
  },
};

/** Aggregated client with all API modules under one namespace. */
export const apiClient = {
  documents,
  conversations,
  chat,
  notes,
  settings,
  models,
  search,
};
