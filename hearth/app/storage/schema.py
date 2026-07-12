"""Database schema DDL for Hearth."""

INIT_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL
        CHECK(doc_type IN (
            'pdf','epub','markdown','audio','text','html','image','other'
        )),
    folder TEXT DEFAULT 'default',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending','processing','ready','error','indexed','failed')),
    file_path TEXT,
    file_size INTEGER DEFAULT 0,
    mime_type TEXT,
    metadata TEXT,
    word_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    content_hash TEXT,
    embedding BLOB,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_content_hash ON chunks(content_hash);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content,
    content='chunks',
    content_rowid='rowid'
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0(
    embedding float[384] distance_metric=cosine
);

CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    title,
    content,
    content='notes',
    content_rowid='rowid'
);

CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    folder TEXT DEFAULT 'default',
    tags TEXT,
    pinned INTEGER DEFAULT 0,
    source_document_id TEXT REFERENCES documents(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_notes_folder ON notes(folder);
CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes(pinned);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    model TEXT DEFAULT 'default',
    system_prompt TEXT DEFAULT '',
    message_count INTEGER DEFAULT 0,
    branch_from TEXT REFERENCES conversations(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
    content TEXT NOT NULL,
    context_docs TEXT,
    citations TEXT,
    token_count INTEGER DEFAULT 0,
    generation_ms INTEGER DEFAULT 0,
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trace_log (
    id TEXT PRIMARY KEY,
    level TEXT NOT NULL CHECK(level IN ('debug','info','warning','error')),
    component TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_trace_log_level ON trace_log(level);
CREATE INDEX IF NOT EXISTS idx_trace_log_component ON trace_log(component);

INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'system');
INSERT OR IGNORE INTO settings (key, value) VALUES ('ollama_base_url', 'http://localhost:11434');
INSERT OR IGNORE INTO settings (key, value) VALUES ('openai_base_url', 'http://localhost:11434/v1');
INSERT OR IGNORE INTO settings (key, value) VALUES ('default_model', 'llama3.2');
INSERT OR IGNORE INTO settings (key, value) VALUES ('embedding_provider', 'local');
INSERT OR IGNORE INTO settings (key, value) VALUES ('chat_provider', 'ollama');
INSERT OR IGNORE INTO settings (key, value) VALUES ('system_prompt', '');
INSERT OR IGNORE INTO settings (key, value) VALUES ('max_tokens', '2048');
INSERT OR IGNORE INTO settings (key, value) VALUES ('temperature', '0.7');
INSERT OR IGNORE INTO settings (key, value) VALUES ('top_k', '40');
INSERT OR IGNORE INTO settings (key, value) VALUES ('top_p', '0.9');
INSERT OR IGNORE INTO settings (key, value) VALUES ('embedding_model', 'gte-small');
INSERT OR IGNORE INTO settings (key, value) VALUES ('chunk_size', '2000');
INSERT OR IGNORE INTO settings (key, value) VALUES ('chunk_overlap', '200');
INSERT OR IGNORE INTO settings (key, value) VALUES ('search_result_count', '5');
INSERT OR IGNORE INTO settings (key, value) VALUES ('pii_filter_enabled', 'false');
"""
