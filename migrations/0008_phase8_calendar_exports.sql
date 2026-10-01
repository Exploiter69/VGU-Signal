PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS calendar_export_tokens (
  token_hash TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  last_used_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_calendar_export_tokens_user
  ON calendar_export_tokens(user_id, expires_at);
