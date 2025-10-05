CREATE TABLE IF NOT EXISTS gen_tracks (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP DEFAULT now(),
  bucket TEXT,
  prompt_id TEXT,
  prompt_text TEXT,
  bpm INT,
  url_wav TEXT,
  url_stems_zip TEXT,
  lufs REAL,
  score_auto REAL
);

CREATE TABLE IF NOT EXISTS ratings (
  id SERIAL PRIMARY KEY,
  gen_track_id INT REFERENCES gen_tracks(id) ON DELETE CASCADE,
  rating INT CHECK (rating IN (-1,0,1)),
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS prompt_bank (
  id TEXT PRIMARY KEY,
  bucket TEXT,
  prompt_text TEXT,
  weight REAL DEFAULT 1.0,
  wins INT DEFAULT 0,
  losses INT DEFAULT 0,
  last_score REAL DEFAULT 0.0
);
