import os
from tools.omdb_fetch import fetch_omdb_data
from tools.tmdb_fetch import fetch_tmdb_data

DEFAULT_POSTER = "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&q=80"

def get_best_poster(title: str, year: str) -> str:
    """Centralized logic to fetch the best available poster."""
    # 1. Try TMDB (which now includes Fanart.tv if available)
    try:
        tmdb_info = fetch_tmdb_data(title, year)
        if tmdb_info and tmdb_info.get("poster_url"):
            return tmdb_info["poster_url"]
    except Exception:
        pass

    # 2. Try OMDb as fallback
    try:
        omdb_info = fetch_omdb_data(title, year)
        if omdb_info and omdb_info.get("Poster") and omdb_info.get("Poster") != "N/A":
            return omdb_info.get("Poster").replace("http://", "https://")
    except Exception:
        pass

    return DEFAULT_POSTER
