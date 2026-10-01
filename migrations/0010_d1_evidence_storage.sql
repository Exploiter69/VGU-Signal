PRAGMA foreign_keys = ON;

-- Durable zero-cost replacement for the billing-gated R2 evidence layer.
-- Each BLOB is kept below D1's 2 MB per-row limit; the application uses 32 KiB chunks.
CREATE TABLE IF NOT EXISTS evidence_blobs (
  evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
  data BLOB NOT NULL,
  PRIMARY KEY (evidence_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_evidence_blobs_evidence
  ON evidence_blobs(evidence_id, chunk_index);

CREATE TABLE IF NOT EXISTS verification_submission_blobs (
  submission_id TEXT NOT NULL REFERENCES verification_submissions(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
  data BLOB NOT NULL,
  PRIMARY KEY (submission_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_verification_submission_blobs_submission
  ON verification_submission_blobs(submission_id, chunk_index);

-- The manifest field is now a generic artifact namespace rather than an R2 prefix.
ALTER TABLE backup_manifests RENAME COLUMN r2_prefix TO artifact_prefix;
