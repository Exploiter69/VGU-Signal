PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  telegram_user_id TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'BLOCKED'))
);

CREATE TABLE IF NOT EXISTS user_preferences (
  user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  program TEXT,
  branch TEXT,
  year INTEGER CHECK (year IS NULL OR (year >= 1 AND year <= 10)),
  semester INTEGER CHECK (semester IS NULL OR (semester >= 1 AND semester <= 20)),
  categories_json TEXT NOT NULL DEFAULT '["DEADLINE","EXAM","FEES","REGISTRATION","NOTICE","EVENT","HOLIDAY","CALENDAR"]',
  digest_enabled INTEGER NOT NULL DEFAULT 1 CHECK (digest_enabled IN (0, 1)),
  reminders_enabled INTEGER NOT NULL DEFAULT 1 CHECK (reminders_enabled IN (0, 1)),
  muted INTEGER NOT NULL DEFAULT 0 CHECK (muted IN (0, 1)),
  quiet_start TEXT,
  quiet_end TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS telegram_sessions (
  user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  flow TEXT NOT NULL,
  step TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  information_item_id TEXT,
  notification_type TEXT NOT NULL CHECK (
    notification_type IN ('REMINDER', 'WEEKLY_DIGEST')
  ),
  scheduled_key TEXT NOT NULL,
  created_at TEXT NOT NULL,
  delivered_at TEXT,
  delivery_status TEXT NOT NULL DEFAULT 'PENDING' CHECK (
    delivery_status IN ('PENDING', 'SENT', 'FAILED', 'SKIPPED')
  ),
  UNIQUE(user_id, information_item_id, notification_type, scheduled_key)
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_status
  ON notifications(user_id, delivery_status);
CREATE INDEX IF NOT EXISTS idx_notifications_schedule
  ON notifications(notification_type, scheduled_key);
