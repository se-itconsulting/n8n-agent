-- Schema for n8n-agent

CREATE TABLE IF NOT EXISTS gen_tracks (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  artist TEXT NOT NULL,
  bpm REAL,
  source TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gen_tracks_source ON gen_tracks(source);

CREATE TABLE IF NOT EXISTS stems (
  id SERIAL PRIMARY KEY,
  track_id INTEGER NOT NULL REFERENCES gen_tracks(id) ON DELETE CASCADE,
  type TEXT NOT NULL, -- drum, bass, lead, vox, etc
  url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ratings (
  id SERIAL PRIMARY KEY,
  track_id INTEGER NOT NULL REFERENCES gen_tracks(id) ON DELETE CASCADE,
  rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  user_name TEXT,
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ratings_track_id ON ratings(track_id);
