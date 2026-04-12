import os
import requests

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


def search_movie(title: str) -> dict | None:
    """Search TMDB for a movie and return the top result."""
    api_key = os.getenv("TMDB_API_KEY")
    try:
        resp = requests.get(
            f"{TMDB_BASE}/search/movie",
            params={"api_key": api_key, "query": title, "language": "en-US", "page": 1},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0] if results else None
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to TMDB: {e}")
        return None


def get_movie_details(tmdb_id: int) -> dict:
    """Get full movie details including credits and videos."""
    api_key = os.getenv("TMDB_API_KEY")

    try:
        resp = requests.get(
            f"{TMDB_BASE}/movie/{tmdb_id}",
            params={"api_key": api_key, "language": "en-US", "append_to_response": "credits,videos"},
            timeout=10,
        )
        resp.raise_for_status()
        details = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch details from TMDB: {e}")
        return {}

    return {
        "id": details.get("id"),
        "title": details.get("title"),
        "overview": details.get("overview"),
        "release_year": details.get("release_date", "")[:4],
        "genres": [g["name"] for g in details.get("genres", [])],
        "runtime": details.get("runtime"),
        "poster_url": f"{TMDB_IMAGE_BASE}{details['poster_path']}" if details.get("poster_path") else None,
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


def get_movie_full(title: str) -> dict | None:
    """Search and return full details for a movie title."""
    result = search_movie(title)
    if not result:
        return None
    return get_movie_details(result["id"])
