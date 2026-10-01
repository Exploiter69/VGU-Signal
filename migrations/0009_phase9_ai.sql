PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ai_embeddings (
  information_item_id TEXT PRIMARY KEY REFERENCES information_items(id) ON DELETE CASCADE,
  model TEXT NOT NULL,
  dimensions INTEGER NOT NULL,
  vector_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ai_embeddings_model ON ai_embeddings(model, updated_at);
