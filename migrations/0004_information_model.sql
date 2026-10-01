PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS information_items (
  id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL UNIQUE REFERENCES claims(id),
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  category TEXT NOT NULL CHECK (
    category IN (
      'DEADLINE',
      'EXAM',
      'FEES',
      'REGISTRATION',
      'NOTICE',
      'EVENT',
      'HOLIDAY',
      'CALENDAR'
    )
  ),
  program TEXT,
  branch TEXT,
  year INTEGER CHECK (year IS NULL OR (year >= 1 AND year <= 10)),
  semester INTEGER CHECK (semester IS NULL OR (semester >= 1 AND semester <= 20)),
  importance TEXT NOT NULL CHECK (
    importance IN ('LOW', 'NORMAL', 'HIGH', 'CRITICAL')
  ),
  urgency TEXT NOT NULL CHECK (
    urgency IN ('NONE', 'UPCOMING', 'SOON', 'IMMEDIATE', 'OVERDUE')
  ),
  published_at TEXT,
  effective_from TEXT,
  effective_until TEXT,
  due_at TEXT,
  starts_at TEXT,
  ends_at TEXT,
  primary_source_url TEXT NOT NULL,
  supersedes_item_id TEXT REFERENCES information_items(id),
  changed_from_item_id TEXT REFERENCES information_items(id),
  corrected_item_id TEXT REFERENCES information_items(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_information_category
  ON information_items(category);
CREATE INDEX IF NOT EXISTS idx_information_scope
  ON information_items(program, branch, year, semester);
CREATE INDEX IF NOT EXISTS idx_information_importance_urgency
  ON information_items(importance, urgency);
CREATE INDEX IF NOT EXISTS idx_information_effective
  ON information_items(effective_from, effective_until);
CREATE INDEX IF NOT EXISTS idx_information_due
  ON information_items(due_at);
CREATE INDEX IF NOT EXISTS idx_information_published
  ON information_items(published_at DESC);

CREATE TABLE IF NOT EXISTS information_source_links (
  item_id TEXT NOT NULL REFERENCES information_items(id),
  source_url TEXT NOT NULL,
  is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
  PRIMARY KEY (item_id, source_url)
);

CREATE INDEX IF NOT EXISTS idx_information_source_links_url
  ON information_source_links(source_url);

CREATE TABLE IF NOT EXISTS information_relationships (
  id TEXT PRIMARY KEY,
  old_item_id TEXT NOT NULL REFERENCES information_items(id),
  new_item_id TEXT NOT NULL REFERENCES information_items(id),
  kind TEXT NOT NULL CHECK (kind IN ('CHANGED', 'SUPERSEDES', 'CORRECTS')),
  created_at TEXT NOT NULL,
  reason TEXT NOT NULL,
  UNIQUE(old_item_id, new_item_id, kind)
);

CREATE INDEX IF NOT EXISTS idx_information_relationships_old
  ON information_relationships(old_item_id);
CREATE INDEX IF NOT EXISTS idx_information_relationships_new
  ON information_relationships(new_item_id);
