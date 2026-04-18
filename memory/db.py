"""
Reelogue Database Layer
-----------------------
Supports two backends:
  • Supabase (cloud)  — used when SUPABASE_URL + SUPABASE_KEY are set (production)
  • SQLite (local)    — fallback for local development

Set SUPABASE_URL and SUPABASE_KEY in your environment / .env file to
enable cloud persistence.
"""

import json
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

_supabase = None  # lazy-initialised Supabase client

if USE_SUPABASE:
    try:
        from supabase import create_client
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Using Supabase for persistent storage")
    except Exception as e:
        logger.error(f"Failed to initialise Supabase client: {e}")
        USE_SUPABASE = False

if not USE_SUPABASE:
    import sqlite3
    DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "reelogue.db"))
    logger.info(f"Using SQLite at {DB_PATH}")


# ---------------------------------------------------------------------------
# SQLite helpers (fallback)
# ---------------------------------------------------------------------------
@contextmanager
def _get_sqlite():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# init_db  — only needed for SQLite; Supabase tables created via dashboard
# ---------------------------------------------------------------------------
def init_db():
    if USE_SUPABASE:
        return  # tables are created via Supabase SQL editor
    with _get_sqlite() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                title TEXT,
                year TEXT,
                m_type TEXT,
                status TEXT,
                user_rating INTEGER,
                user_comment TEXT,
                poster_url TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                title TEXT,
                rating INTEGER,
                review_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                session_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')


# ===================================================================
# WATCHLIST
# ===================================================================

def add_to_watchlist(session_id, title, year, m_type, status, user_rating, user_comment, poster_url):
    row = {
        "session_id": session_id,
        "title": title,
        "year": year,
        "m_type": m_type,
        "status": status,
        "user_rating": user_rating,
        "user_comment": user_comment,
        "poster_url": poster_url,
    }
    if USE_SUPABASE:
        _supabase.table("watchlist").insert(row).execute()
    else:
        with _get_sqlite() as conn:
            conn.execute(
                "INSERT INTO watchlist (session_id, title, year, m_type, status, user_rating, user_comment, poster_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, title, year, m_type, status, user_rating, user_comment, poster_url)
            )


def get_watchlist(session_id, status_filter=None):
    if USE_SUPABASE:
        q = _supabase.table("watchlist").select("*").eq("session_id", session_id)
        if status_filter:
            q = q.eq("status", status_filter)
        result = q.order("added_at", desc=True).execute()
        return result.data or []
    else:
        with _get_sqlite() as conn:
            if status_filter:
                rows = conn.execute("SELECT * FROM watchlist WHERE session_id = ? AND status = ? ORDER BY added_at DESC", (session_id, status_filter)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM watchlist WHERE session_id = ? ORDER BY added_at DESC", (session_id,)).fetchall()
            return [dict(row) for row in rows]


def remove_from_watchlist(session_id, title):
    if USE_SUPABASE:
        _supabase.table("watchlist").delete().eq("session_id", session_id).eq("title", title).execute()
    else:
        with _get_sqlite() as conn:
            conn.execute("DELETE FROM watchlist WHERE session_id = ? AND title = ?", (session_id, title))


# ===================================================================
# USER REVIEWS
# ===================================================================

def add_user_review(session_id, title, rating, review_text):
    row = {
        "session_id": session_id,
        "title": title,
        "rating": rating,
        "review_text": review_text,
    }
    if USE_SUPABASE:
        _supabase.table("user_reviews").insert(row).execute()
    else:
        with _get_sqlite() as conn:
            conn.execute(
                "INSERT INTO user_reviews (session_id, title, rating, review_text) VALUES (?, ?, ?, ?)",
                (session_id, title, rating, review_text)
            )


def get_user_reviews(session_id):
    if USE_SUPABASE:
        result = _supabase.table("user_reviews").select("*").eq("session_id", session_id).order("created_at", desc=True).execute()
        return result.data or []
    else:
        with _get_sqlite() as conn:
            rows = conn.execute("SELECT * FROM user_reviews WHERE session_id = ? ORDER BY created_at DESC", (session_id,)).fetchall()
            return [dict(row) for row in rows]


# ===================================================================
# USER PROFILES
# ===================================================================

def save_user_profile(session_id, profile_dict):
    """Persist a user profile."""
    if USE_SUPABASE:
        _supabase.table("user_profiles").upsert({
            "session_id": session_id,
            "profile_json": profile_dict,  # JSONB column — pass dict directly
        }).execute()
    else:
        profile_json = json.dumps(profile_dict)
        with _get_sqlite() as conn:
            conn.execute(
                "INSERT INTO user_profiles (session_id, profile_json, updated_at) "
                "VALUES (?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(session_id) DO UPDATE SET profile_json = excluded.profile_json, updated_at = CURRENT_TIMESTAMP",
                (session_id, profile_json)
            )
    logger.info(f"Profile saved for session {session_id}")


def load_user_profile(session_id):
    """Load a user profile. Returns dict or None."""
    if USE_SUPABASE:
        result = _supabase.table("user_profiles").select("profile_json").eq("session_id", session_id).execute()
        if result.data:
            pj = result.data[0]["profile_json"]
            # JSONB returns dict directly; TEXT returns string
            return pj if isinstance(pj, dict) else json.loads(pj)
        return None
    else:
        with _get_sqlite() as conn:
            row = conn.execute(
                "SELECT profile_json FROM user_profiles WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            if row:
                return json.loads(row["profile_json"])
        return None


# ===================================================================
# RESET (wipe all data for a session)
# ===================================================================

def reset_session_data(session_id):
    """Delete ALL data for a session: profile, watchlist, reviews."""
    if USE_SUPABASE:
        _supabase.table("user_profiles").delete().eq("session_id", session_id).execute()
        _supabase.table("watchlist").delete().eq("session_id", session_id).execute()
        _supabase.table("user_reviews").delete().eq("session_id", session_id).execute()
    else:
        with _get_sqlite() as conn:
            conn.execute("DELETE FROM user_profiles WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM watchlist WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM user_reviews WHERE session_id = ?", (session_id,))
    logger.info(f"All data reset for session {session_id}")
