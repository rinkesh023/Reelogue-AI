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

from memory.db import init_db, add_to_watchlist, get_watchlist, remove_from_watchlist, add_user_review, get_user_reviews
from agents.recommendation_agent import get_recommendations
from agents.review_agent import review_movie
from agents.judge_agent import evaluate_review
from agents.search_agent import agentic_search_loop
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

# In-memory session store (use Redis/Supabase in production)
sessions: dict[str, UserProfile] = {}


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
    """Create or update a user taste profile."""
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
    return {"status": "ok", "session_id": data.session_id}


@app.post("/recommendations")
def recommendations(body: dict):
    """Get personalised recommendations for a session."""
    session_id = body.get("session_id")
    profile = sessions.get(session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Session not found. Create a profile first.")

    try:
        recs = get_recommendations(profile)
        return {"recommendations": recs}
    except Exception as e:
        if "429" in str(e) or "ResourceExhausted" in str(e):
            raise HTTPException(status_code=429, detail=f"Rate Limit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/review")
def review(req: ReviewRequest):
    """Get a full review for a specific title."""
    profile = sessions.get(req.session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Session not found.")

    try:
        result = review_movie(req.title, req.year, profile)
        return result
    except Exception as e:
        if "429" in str(e) or "ResourceExhausted" in str(e):
            raise HTTPException(status_code=429, detail=f"Rate Limit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
def search(req: SearchRequest):
    """Agentic search for a global query."""
    try:
        profile = sessions.get(req.session_id)
        result = agentic_search_loop(req.query, profile or UserProfile())
        return result
    except Exception as e:
        if "429" in str(e) or "ResourceExhausted" in str(e):
            raise HTTPException(status_code=429, detail=f"Rate Limit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/judge")
def judge(req: JudgeRequest):
    """Judge evaluation for an AI review."""
    try:
        profile = sessions.get(req.session_id)
        result = evaluate_review(req.review_data, profile or UserProfile())
        return result
    except Exception as e:
        if "429" in str(e) or "ResourceExhausted" in str(e):
            raise HTTPException(status_code=429, detail=f"Rate Limit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rate")
def rate(data: RatingInput):
    """Submit a rating to improve the user's taste profile."""
    profile = sessions.get(data.session_id)
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
    profile = sessions.get(data.session_id)
    if profile:
        profile.add_rating(data.title, data.rating, data.feedback)
    return {"status": "ok"}

@app.get("/user_reviews/{session_id}")
def view_user_reviews(session_id: str):
    return {"reviews": get_user_reviews(session_id)}


@app.get("/health")
def health():
    return {"status": "Reelogue is running"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
