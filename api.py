"""
Reelogue FastAPI backend — for web/mobile deployment
Run with: uvicorn api:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

from memory.db import (
    init_db, add_to_watchlist, get_watchlist, remove_from_watchlist,
    add_user_review, get_user_reviews, save_user_profile, load_user_profile,
    reset_session_data
)
from agents.recommendation_agent import get_recommendations
from agents.review_agent import review_movie
from agents.judge_agent import evaluate_review
from agents.chat_search_agent import get_chat_search_results
from memory.user_profile import UserProfile

app = FastAPI(title="Reelogue API", version="1.0.0")

# Initialize SQLite database file on startup
init_db()

# Mount a static folder for the frontend at the root path, if it exists
if os.path.exists("static"):
    app.mount("/sub", StaticFiles(directory="static", html=True), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session cache — backed by SQLite for persistence
sessions: dict[str, UserProfile] = {}


def _get_profile(session_id: str) -> UserProfile | None:
    """Get profile from cache, falling back to SQLite."""
    if session_id in sessions:
        return sessions[session_id]
    # Try loading from database
    data = load_user_profile(session_id)
    if data:
        profile = UserProfile(
            name=data.get("name", ""),
            favourite_genres=data.get("favourite_genres", []),
            favourite_films=data.get("favourite_films", []),
            favourite_directors=data.get("favourite_directors", []),
            mood=data.get("mood", ""),
            viewing_context=data.get("viewing_context", ""),
            content_type=data.get("content_type", "both"),
            language_preference=data.get("language_preference", []),
            disliked_genres=data.get("disliked_genres", []),
            streaming_services=data.get("streaming_services", []),
        )
        sessions[session_id] = profile
        return profile
    return None


class ProfileInput(BaseModel):
    session_id: str
    name: str = ""
    favourite_genres: list[str] = []
    favourite_films: list[str] = []
    favourite_directors: list[str] = []
    mood: str = ""
    viewing_context: str = ""
    content_type: str = "both"
    language_preference: list[str] = []
    disliked_genres: list[str] = []
    streaming_services: list[str] = []


class ReviewRequest(BaseModel):
    session_id: str
    title: str
    year: str = ""


class RatingInput(BaseModel):
    session_id: str
    title: str
    rating: int
    feedback: str = ""

class SearchRequest(BaseModel):
    session_id: str
    query: str

class JudgeRequest(BaseModel):
    session_id: str
    review_data: dict

class WatchlistInput(BaseModel):
    session_id: str
    title: str
    year: str = ""
    m_type: str = "Movie"
    status: str = "Want to Watch"
    user_rating: int = 0
    user_comment: str = ""
    poster_url: str = ""


@app.post("/profile")
def create_profile(data: ProfileInput):
    """Create or update a user taste profile (persisted to SQLite)."""
    profile = UserProfile(
        name=data.name,
        favourite_genres=data.favourite_genres,
        favourite_films=data.favourite_films,
        favourite_directors=data.favourite_directors,
        mood=data.mood,
        viewing_context=data.viewing_context,
        content_type=data.content_type,
        language_preference=data.language_preference,
        disliked_genres=data.disliked_genres,
        streaming_services=data.streaming_services,
    )
    sessions[data.session_id] = profile
    # Persist to SQLite so it survives server restarts
    save_user_profile(data.session_id, {
        "name": data.name,
        "favourite_genres": data.favourite_genres,
        "favourite_films": data.favourite_films,
        "favourite_directors": data.favourite_directors,
        "mood": data.mood,
        "viewing_context": data.viewing_context,
        "content_type": data.content_type,
        "language_preference": data.language_preference,
        "disliked_genres": data.disliked_genres,
        "streaming_services": data.streaming_services,
    })
    return {"status": "ok", "session_id": data.session_id}


@app.get("/profile/{session_id}")
def get_profile(session_id: str):
    """Load a persisted user profile by session ID."""
    data = load_user_profile(session_id)
    if data:
        return {"profile": data}
    raise HTTPException(status_code=404, detail="No saved profile found for this session.")


@app.post("/recommendations")
def recommendations(body: dict):
    """Get personalised recommendations for a session."""
    session_id = body.get("session_id")
    profile = _get_profile(session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Session not found. Create a profile first.")

    try:
        recs = get_recommendations(profile)
        return {"recommendations": recs}
    except Exception as e:
        if "429" in str(e) or "RateLimit" in str(e):
            raise HTTPException(status_code=429, detail=f"Groq API Rate Limit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/review")
def review(req: ReviewRequest):
    """Get a full review for a specific title."""
    # Profile is optional — use blank profile if no session exists (e.g. chat_search flow)
    profile = _get_profile(req.session_id) or UserProfile()

    try:
        result = review_movie(req.title, req.year, profile)
        return result
    except Exception as e:
        if "429" in str(e) or "RateLimit" in str(e):
            raise HTTPException(status_code=429, detail=f"Groq API Rate Limit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat_search")
def chat_search(req: SearchRequest):
    """Conversational search returning a list of movies to review."""
    try:
        result = get_chat_search_results(req.query)
        return {"results": result}
    except Exception as e:
        if "429" in str(e) or "RateLimit" in str(e):
            raise HTTPException(status_code=429, detail=f"Groq API Rate Limit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/judge")
def judge(req: JudgeRequest):
    """Judge evaluation for an AI review."""
    try:
        profile = _get_profile(req.session_id)
        result = evaluate_review(req.review_data, profile or UserProfile())
        return result
    except Exception as e:
        if "429" in str(e) or "RateLimit" in str(e):
            raise HTTPException(status_code=429, detail=f"Groq API Rate Limit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rate")
def rate(data: RatingInput):
    """Submit a rating to improve the user's taste profile."""
    profile = _get_profile(data.session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Session not found.")

    profile.add_rating(data.title, data.rating, data.feedback)
    return {"status": "ok", "message": "Taste profile updated."}

@app.post("/watchlist")
def add_watchlist(data: WatchlistInput):
    add_to_watchlist(data.session_id, data.title, data.year, data.m_type, data.status, data.user_rating, data.user_comment, data.poster_url)
    return {"status": "ok"}

@app.get("/watchlist/{session_id}")
def view_watchlist(session_id: str, status: str = None):
    return {"watchlist": get_watchlist(session_id, status)}

@app.delete("/watchlist/{session_id}/{title}")
def delete_watchlist(session_id: str, title: str):
    remove_from_watchlist(session_id, title)
    return {"status": "ok"}

@app.post("/user_reviews")
def submit_user_review(data: RatingInput):
    add_user_review(data.session_id, data.title, data.rating, data.feedback)
    # Also feed it to the AI agent taste profile logic
    profile = _get_profile(data.session_id)
    if profile:
        profile.add_rating(data.title, data.rating, data.feedback)
    return {"status": "ok"}

@app.get("/user_reviews/{session_id}")
def view_user_reviews(session_id: str):
    return {"reviews": get_user_reviews(session_id)}


@app.delete("/reset/{session_id}")
def reset_session(session_id: str):
    """Wipe ALL data for a session: profile, watchlist, reviews."""
    reset_session_data(session_id)
    # Clear from in-memory cache too
    sessions.pop(session_id, None)
    return {"status": "ok", "message": "All data has been reset."}


@app.get("/health")
def health():
    return {"status": "Reelogue is running"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
