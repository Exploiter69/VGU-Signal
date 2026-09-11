PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  source_class TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(id),
  source_url TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  http_status INTEGER NOT NULL,
  content_type TEXT NOT NULL,
  raw_content_hash TEXT NOT NULL,
  raw_content_ref TEXT,
  extracted_text_hash TEXT,
  parser_version TEXT,
  http_last_modified TEXT,
  http_etag TEXT,
  UNIQUE(source_id, raw_content_hash)
);

CREATE INDEX IF NOT EXISTS idx_evidence_source_fetched
  ON evidence(source_id, fetched_at DESC);
