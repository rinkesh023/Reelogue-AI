import os
import requests

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


def search_movie(title: str, year: str = "") -> dict | None:
    """Search TMDB for a movie and return the top result. Falls back to TV search."""
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        return None

    # Try movie search first
    try:
        params = {"api_key": api_key, "query": title, "language": "en-US", "page": 1}
        if year:
            params["primary_release_year"] = year
        resp = requests.get(f"{TMDB_BASE}/search/movie", params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            return {"result": results[0], "media_type": "movie"}
    except Exception as e:
        print(f"TMDB movie search failed: {e}")

    # Fallback to TV series search (catches Moon Knight, series, etc.)
    try:
        params = {"api_key": api_key, "query": title, "language": "en-US", "page": 1}
        resp = requests.get(f"{TMDB_BASE}/search/tv", params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            return {"result": results[0], "media_type": "tv"}
    except Exception as e:
        print(f"TMDB TV search failed: {e}")

    return None


def get_movie_details(tmdb_id: int, media_type: str = "movie") -> dict:
    """Get full movie/TV details including credits and videos."""
    api_key = os.getenv("TMDB_API_KEY")

    try:
        resp = requests.get(
            f"{TMDB_BASE}/{media_type}/{tmdb_id}",
            params={"api_key": api_key, "language": "en-US", "append_to_response": "credits,videos"},
            timeout=10,
        )
        resp.raise_for_status()
        details = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch details from TMDB: {e}")
        return {}

    # Build poster URL — prioritized Fanart.tv if available, else TMDB
    try:
        from tools.fanart_fetch import get_fanart_poster
    except ImportError:
        from .fanart_fetch import get_fanart_poster
    
    fanart_poster = get_fanart_poster(details.get("id"))
    
    if fanart_poster:
        poster_url = fanart_poster
    else:
        poster_path = details.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

    return {
        "id": details.get("id"),
        "title": details.get("title") or details.get("name"),
        "overview": details.get("overview"),
        "release_year": (details.get("release_date") or details.get("first_air_date") or "")[:4],
        "genres": [g["name"] for g in details.get("genres", [])],
        "runtime": details.get("runtime"),
        "poster_url": poster_url,
        "backdrop_url": f"https://image.tmdb.org/t/p/w1280{details['backdrop_path']}" if details.get("backdrop_path") else None,
        "cast": [m["name"] for m in details.get("credits", {}).get("cast", [])[:5]],
        "director": next(
            (m["name"] for m in details.get("credits", {}).get("crew", []) if m["job"] == "Director"),
            "Unknown",
        ),
        "trailer_key": next(
            (v["key"] for v in details.get("videos", {}).get("results", [])
             if v["type"] == "Trailer" and v["site"] == "YouTube"),
            None,
        ),
        "tmdb_rating": round(details.get("vote_average", 0), 1),
        "vote_count": details.get("vote_count", 0),
    }


def fetch_tmdb_data(title: str, year: str = "") -> dict | None:
    """Search and return full details for a movie or TV title."""
    found = search_movie(title, year)
    if not found:
        return None
    result = found["result"]
    media_type = found["media_type"]
    return get_movie_details(result["id"], media_type)


# Keep backward-compat alias used by review_agent etc.
def get_movie_full(title: str, year: str = "") -> dict | None:
    return fetch_tmdb_data(title, year)
