PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS acquisition_runs (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(id),
  started_at TEXT NOT NULL,
  finished_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('FETCHED', 'UNCHANGED', 'CHANGED', 'FAILED')),
  evidence_id TEXT REFERENCES evidence(id),
  last_known_good_evidence_id TEXT REFERENCES evidence(id),
  error TEXT
);

CREATE INDEX IF NOT EXISTS idx_acquisition_runs_source_finished
  ON acquisition_runs(source_id, finished_at DESC);

CREATE INDEX IF NOT EXISTS idx_evidence_source_hash
  ON evidence(source_id, raw_content_hash);
