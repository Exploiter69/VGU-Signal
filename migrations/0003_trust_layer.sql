PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  evidence_id TEXT NOT NULL REFERENCES evidence(id),
  source_id TEXT NOT NULL REFERENCES sources(id),
  canonical_url TEXT NOT NULL,
  title TEXT NOT NULL,
  published_at TEXT,
  body_text TEXT NOT NULL DEFAULT '',
  parser_version TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'PARSED',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_source_url
  ON documents(source_id, canonical_url);

CREATE TABLE IF NOT EXISTS claims (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(id),
  evidence_id TEXT NOT NULL REFERENCES evidence(id),
  source_id TEXT NOT NULL REFERENCES sources(id),
  statement TEXT NOT NULL,
  normalized_statement TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'UNVERIFIED',
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  effective_from TEXT,
  effective_until TEXT,
  supersedes_claim_id TEXT REFERENCES claims(id),
  correction_of_claim_id TEXT REFERENCES claims(id)
);

CREATE INDEX IF NOT EXISTS idx_claims_fingerprint ON claims(fingerprint);
CREATE INDEX IF NOT EXISTS idx_claims_source_last_seen ON claims(source_id, last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_claims_state ON claims(state);

CREATE TABLE IF NOT EXISTS claim_evidence (
  claim_id TEXT NOT NULL REFERENCES claims(id),
  evidence_id TEXT NOT NULL REFERENCES evidence(id),
  role TEXT NOT NULL,
  PRIMARY KEY (claim_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS claim_relationships (
  id TEXT PRIMARY KEY,
  left_claim_id TEXT NOT NULL REFERENCES claims(id),
  right_claim_id TEXT NOT NULL REFERENCES claims(id),
  kind TEXT NOT NULL,
  created_at TEXT NOT NULL,
  reason TEXT NOT NULL,
  similarity REAL,
  CHECK (similarity IS NULL OR (similarity >= 0 AND similarity <= 1))
);

CREATE INDEX IF NOT EXISTS idx_claim_relationships_left
  ON claim_relationships(left_claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_relationships_right
  ON claim_relationships(right_claim_id);

CREATE TABLE IF NOT EXISTS verification_decisions (
  claim_id TEXT NOT NULL REFERENCES claims(id),
  state TEXT NOT NULL,
  reason TEXT NOT NULL,
  decided_at TEXT NOT NULL,
  PRIMARY KEY (claim_id, decided_at)
);

CREATE TABLE IF NOT EXISTS correction_history (
  id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL REFERENCES claims(id),
  correction_claim_id TEXT NOT NULL REFERENCES claims(id),
  created_at TEXT NOT NULL,
  reason TEXT NOT NULL
);
