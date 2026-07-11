/* ── Document Types ──────────────────────────────────────────── */

export type DocType = 'pdf' | 'image' | 'audio' | 'note' | 'text';

export interface UploadProgress {
  loaded: number;
  total: number;
}
export type DocStatus = 'pending' | 'processing' | 'ready' | 'error';

export interface Document {
  id: string;
  title: string;
  doc_type: DocType;
  status: DocStatus;
  file_size: number;
  file_path: string;
  folder: string;
  page_count: number | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
  error_message: string | null;
}

export interface Chunk {
  id: string;
  document_id: string;
  index: number;
  content: string;
  embedding: number[] | null;
  created_at: string;
}

/* ── Conversation Types ──────────────────────────────────────── */

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: Citation[] | null;
  token_count: number | null;
  generation_ms: number | null;
  created_at: string;
}

export interface Citation {
  id: string;
  doc_title: string;
  text: string;
  score: number;
  verified: boolean;
  color: 'green' | 'amber' | 'red';
}

export interface ChatRequest {
  conversation_id: string;
  query: string;
  context_docs?: string[];
}

export interface ChatResponse {
  conversation_id: string;
  message: Message;
  citations: Citation[];
  token_count: number;
  generation_ms: number;
}

/* ── Note Types ──────────────────────────────────────────────── */

export interface Note {
  id: string;
  title: string;
  content: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

/* ── Settings Types ──────────────────────────────────────────── */

export interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  ollama_base_url: string;
  openai_base_url: string;
  default_model: string;
  embedding_provider: 'local' | 'ollama' | 'openai';
  chat_provider: 'local' | 'ollama' | 'openai';
  system_prompt: string;
  max_tokens: number;
  temperature: number;
  top_k: number;
  top_p: number;
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
  search_result_count: number;
  pii_filter_enabled: boolean;
}

export interface ModelStatus {
  name: string;
  loaded: boolean;
  model_type: 'chat' | 'embedding' | 'vision';
  size: string;
  modified_at: string;
}

/* ── SSE Event Types ─────────────────────────────────────────── */

export type SSEEventType = 'status' | 'token' | 'done' | 'error';

export interface SSEEvent {
  type: SSEEventType;
}

export interface StatusEvent extends SSEEvent {
  type: 'status';
  status: string;
}

export interface TokenEvent extends SSEEvent {
  type: 'token';
  token: string;
}

export interface DoneEvent extends SSEEvent {
  type: 'done';
  conversation_id: string;
  message_id: string;
  token_count: number;
  generation_ms: number;
}

export interface ErrorEvent extends SSEEvent {
  type: 'error';
  code: string;
  message: string;
}
