CREATE TABLE IF NOT EXISTS sessions (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL,
  type        TEXT NOT NULL CHECK (type IN ('pdf','web')),
  title       TEXT NOT NULL,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS documents (
  session_id    TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
  filename      TEXT NOT NULL,
  size_bytes    INTEGER NOT NULL,
  page_count    INTEGER,
  n_chunks      INTEGER,
  status        TEXT NOT NULL CHECK (status IN ('processing','ready','failed')),
  stage         TEXT NOT NULL,            -- parsing|chunking|embedding|indexing|done|failed
  progress      INTEGER NOT NULL DEFAULT 0,
  error_code    TEXT,
  error_message TEXT,
  embed_model   TEXT,
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
  id           TEXT PRIMARY KEY,
  session_id   TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  role         TEXT NOT NULL CHECK (role IN ('user','assistant')),
  content      TEXT NOT NULL,
  sources_json TEXT,
  model_used   TEXT,
  fallback     INTEGER NOT NULL DEFAULT 0,
  grounded     INTEGER,
  created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);
