import sqlite3
import json
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "reelogue.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    with get_db() as conn:
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

def add_to_watchlist(session_id, title, year, m_type, status, user_rating, user_comment, poster_url):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO watchlist (session_id, title, year, m_type, status, user_rating, user_comment, poster_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (session_id, title, year, m_type, status, user_rating, user_comment, poster_url)
        )

def get_watchlist(session_id, status_filter=None):
    with get_db() as conn:
        if status_filter:
            rows = conn.execute("SELECT * FROM watchlist WHERE session_id = ? AND status = ? ORDER BY added_at DESC", (session_id, status_filter)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM watchlist WHERE session_id = ? ORDER BY added_at DESC", (session_id,)).fetchall()
        return [dict(row) for row in rows]

def remove_from_watchlist(session_id, title):
    with get_db() as conn:
        conn.execute("DELETE FROM watchlist WHERE session_id = ? AND title = ?", (session_id, title))

def add_user_review(session_id, title, rating, review_text):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO user_reviews (session_id, title, rating, review_text) VALUES (?, ?, ?, ?)",
            (session_id, title, rating, review_text)
        )

def get_user_reviews(session_id):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM user_reviews WHERE session_id = ? ORDER BY created_at DESC", (session_id,)).fetchall()
        return [dict(row) for row in rows]
