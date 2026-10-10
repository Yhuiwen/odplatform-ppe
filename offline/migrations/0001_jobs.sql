CREATE TABLE IF NOT EXISTS jobs(
  job_id TEXT PRIMARY KEY, media_type TEXT NOT NULL CHECK(media_type IN ('image','video')),
  original_filename TEXT NOT NULL, input_sha256 TEXT, input_size_bytes INTEGER,
  input_mime TEXT, input_codec TEXT, input_width INTEGER, input_height INTEGER, input_fps REAL,
  input_frame_count INTEGER, input_duration_seconds REAL, has_audio INTEGER,
  audio_discard_confirmed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL, progress_percent REAL, processed_frames INTEGER NOT NULL DEFAULT 0,
  total_frames INTEGER, created_at TEXT NOT NULL, started_at TEXT, updated_at TEXT NOT NULL,
  completed_at TEXT, error_code TEXT, error_message TEXT,
  artifact_manifest TEXT NOT NULL DEFAULT '{}', schema_version INTEGER NOT NULL DEFAULT 1,
  CHECK(processed_frames >= 0), CHECK(progress_percent IS NULL OR progress_percent BETWEEN 0 AND 100)
);
CREATE INDEX IF NOT EXISTS idx_offline_jobs_created ON jobs(created_at DESC, job_id DESC);
CREATE INDEX IF NOT EXISTS idx_offline_jobs_status ON jobs(status, created_at);
