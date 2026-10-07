CREATE TABLE IF NOT EXISTS users (
 id UUID PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','operator','visitor')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS visitor_expires_at TIMESTAMPTZ;
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check CHECK(role IN ('admin','operator','visitor'));
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 expires_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS invitations (
 token_hash TEXT PRIMARY KEY, created_by UUID NOT NULL REFERENCES users(id),
 expires_at TIMESTAMPTZ NOT NULL, used_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS sources (
 id UUID PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('upload','webcam','stream')),
 stream_url TEXT, location TEXT NOT NULL, latitude DOUBLE PRECISION CHECK(latitude BETWEEN -90 AND 90),
 longitude DOUBLE PRECISION CHECK(longitude BETWEEN -180 AND 180), status TEXT NOT NULL DEFAULT 'idle',
 last_error TEXT, created_by UUID NOT NULL REFERENCES users(id), created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 last_frame_at TIMESTAMPTZ, tracks JSONB NOT NULL DEFAULT '[]', fps DOUBLE PRECISION NOT NULL DEFAULT 0,
 archived BOOLEAN NOT NULL DEFAULT false
);
CREATE TABLE IF NOT EXISTS jobs (
 id UUID PRIMARY KEY, source_id UUID NOT NULL REFERENCES sources(id), path TEXT NOT NULL,
 original_name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued', progress REAL NOT NULL DEFAULT 0,
 processed_frames INTEGER NOT NULL DEFAULT 0, total_frames INTEGER NOT NULL DEFAULT 0,
 error TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), finished_at TIMESTAMPTZ
);
ALTER TABLE sources ADD COLUMN IF NOT EXISTS lease_expires_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS jobs_queue ON jobs(status,created_at);
CREATE TABLE IF NOT EXISTS incidents (
 id UUID PRIMARY KEY, source_id UUID NOT NULL REFERENCES sources(id), job_id UUID REFERENCES jobs(id),
 status TEXT NOT NULL DEFAULT 'review' CHECK(status IN ('review','confirmed','dismissed','resolved')),
 score REAL NOT NULL CHECK(score BETWEEN 0 AND 1), signals JSONB NOT NULL,
 snapshot_path TEXT NOT NULL, video_seconds DOUBLE PRECISION,
 detected_at TIMESTAMPTZ NOT NULL DEFAULT now(), reviewed_by UUID REFERENCES users(id),
 reviewed_at TIMESTAMPTZ, notes TEXT NOT NULL DEFAULT '', ai_summary TEXT, ai_model TEXT,
 ai_generated_at TIMESTAMPTZ, ai_error TEXT
);
CREATE TABLE IF NOT EXISTS alert_targets (
 id UUID PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL, secret TEXT NOT NULL,
 enabled BOOLEAN NOT NULL DEFAULT true, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS alert_deliveries (
 id UUID PRIMARY KEY, incident_id UUID NOT NULL REFERENCES incidents(id),
 target_id UUID NOT NULL REFERENCES alert_targets(id), status TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0, response_code INTEGER, last_error TEXT,
 next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT now(), created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 delivered_at TIMESTAMPTZ, UNIQUE(incident_id,target_id)
);
CREATE TABLE IF NOT EXISTS audit_log (
 id BIGSERIAL PRIMARY KEY, actor_id UUID REFERENCES users(id), action TEXT NOT NULL,
 resource_id UUID, detail JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS events (
 id BIGSERIAL PRIMARY KEY, kind TEXT NOT NULL, payload JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS events_created ON events(created_at);
ALTER TABLE events ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES users(id);
