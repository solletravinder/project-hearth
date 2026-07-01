import type {
  Document,
  Conversation,
  Message,
  Note,
  AppSettings,
  ModelStatus,
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
  status?: string;
  page?: number;
  per_page?: number;
}

export const documents = {
  list(params?: ListDocsParams): Promise<{ documents: Document[]; total: number }> {
    const qs = new URLSearchParams();
    if (params?.folder) qs.set('folder', params.folder);
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
    return request('/documents', {
      method: 'POST',
      body: form,
    });
  },

  delete(id: string): Promise<void> {
    return request(`/documents/${id}`, { method: 'DELETE' });
  },

  reindex(id: string): Promise<Document> {
    return request(`/documents/${id}/reindex`, { method: 'POST' });
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
  get(): Promise<AppSettings> {
    return request('/settings');
  },

  update(data: Partial<AppSettings>): Promise<AppSettings> {
    return request('/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};

/* ── Models API ──────────────────────────────────────────────── */

export const models = {
  status(): Promise<{ models: ModelStatus[] }> {
    return request('/models/status');
  },

  profiles(): Promise<{ profiles: string[] }> {
    return request('/models/profiles');
  },

  unload(name: string): Promise<void> {
    return request(`/models/${encodeURIComponent(name)}/unload`, { method: 'POST' });
  },
};
