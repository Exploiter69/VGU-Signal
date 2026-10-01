PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS verification_submissions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  telegram_chat_id TEXT NOT NULL,
  telegram_message_id INTEGER NOT NULL,
  intake_kind TEXT NOT NULL CHECK (intake_kind IN ('FORWARDED_TEXT','TEXT','IMAGE','PDF')),
  content_type TEXT,
  file_name TEXT,
  object_key TEXT,
  submitted_text TEXT,
  extracted_text TEXT,
  extraction_kind TEXT,
  status TEXT NOT NULL DEFAULT 'QUEUED'
    CHECK (status IN ('QUEUED','PROCESSING','MATCHED','CONFLICTING','UNVERIFIED','REVIEW','FAILED')),
  result_summary TEXT,
  created_at TEXT NOT NULL,
  processed_at TEXT,
  UNIQUE(telegram_chat_id, telegram_message_id)
);

CREATE INDEX IF NOT EXISTS idx_verification_submissions_status
  ON verification_submissions(status, created_at);

CREATE TABLE IF NOT EXISTS verification_matches (
  submission_id TEXT NOT NULL REFERENCES verification_submissions(id) ON DELETE CASCADE,
  information_item_id TEXT NOT NULL REFERENCES information_items(id),
  score REAL NOT NULL CHECK (score >= 0 AND score <= 1),
  match_reason TEXT NOT NULL,
  matched_at TEXT NOT NULL,
  PRIMARY KEY (submission_id, information_item_id)
);

CREATE INDEX IF NOT EXISTS idx_verification_matches_submission
  ON verification_matches(submission_id, score DESC);

CREATE TABLE IF NOT EXISTS moderator_review_queue (
  id TEXT PRIMARY KEY,
  submission_id TEXT NOT NULL UNIQUE REFERENCES verification_submissions(id) ON DELETE CASCADE,
  reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'OPEN'
    CHECK (status IN ('OPEN','RESOLVED','DISMISSED')),
  created_at TEXT NOT NULL,
  resolved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_moderator_review_queue_status
  ON moderator_review_queue(status, created_at);
