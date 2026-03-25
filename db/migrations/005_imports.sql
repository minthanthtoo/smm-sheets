-- Import history
CREATE TABLE IF NOT EXISTS import_jobs (
  import_id TEXT PRIMARY KEY,
  requested_at TEXT NOT NULL,
  completed_at TEXT,
  region TEXT,
  status TEXT NOT NULL,
  input_dir TEXT,
  file_names TEXT,
  error_message TEXT,
  requested_by TEXT
);

CREATE INDEX IF NOT EXISTS ix_import_jobs_requested_at
  ON import_jobs (requested_at);
