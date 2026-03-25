-- Export history (Excel regeneration)
CREATE TABLE IF NOT EXISTS export_jobs (
  export_id TEXT PRIMARY KEY,
  requested_at TEXT NOT NULL,
  completed_at TEXT,
  region TEXT,
  status TEXT NOT NULL,
  file_path TEXT,
  error_message TEXT,
  requested_by TEXT
);

CREATE INDEX IF NOT EXISTS ix_export_jobs_requested_at
  ON export_jobs (requested_at);
