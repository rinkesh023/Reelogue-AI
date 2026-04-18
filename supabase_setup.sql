-- ============================================================
-- Reelogue — Supabase Table Setup
-- ============================================================
-- Run this in your Supabase project:
--   Dashboard → SQL Editor → New Query → Paste & Run
-- ============================================================

-- 1. Watchlist table
CREATE TABLE IF NOT EXISTS watchlist (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    title TEXT NOT NULL,
    year TEXT DEFAULT '',
    m_type TEXT DEFAULT 'Movie',
    status TEXT DEFAULT 'Want to Watch',
    user_rating INTEGER DEFAULT 0,
    user_comment TEXT DEFAULT '',
    poster_url TEXT DEFAULT '',
    added_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. User reviews table
CREATE TABLE IF NOT EXISTS user_reviews (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    title TEXT NOT NULL,
    rating INTEGER DEFAULT 0,
    review_text TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. User profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    session_id TEXT PRIMARY KEY,
    profile_json JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Indexes for faster lookups by session_id
CREATE INDEX IF NOT EXISTS idx_watchlist_session ON watchlist(session_id);
CREATE INDEX IF NOT EXISTS idx_reviews_session ON user_reviews(session_id);

-- 5. Enable Row Level Security (required by Supabase)
ALTER TABLE watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- 6. Allow all operations via anon key (no auth in this app)
CREATE POLICY "Allow all operations on watchlist" ON watchlist
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations on user_reviews" ON user_reviews
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations on user_profiles" ON user_profiles
    FOR ALL USING (true) WITH CHECK (true);
