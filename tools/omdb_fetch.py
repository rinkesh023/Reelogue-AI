import os
import requests
from dotenv import load_dotenv

load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

def fetch_omdb_data(title: str, year: str = "") -> dict:
    """
    Fetch movie metadata from OMDb API using fuzzy search to handle partial/foreign titles.
    """
    if not OMDB_API_KEY:
        print("Warning: OMDB_API_KEY is not set.")
        return {}

    # Use search endpoint (&s=) for better fuzzy matching
    search_url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={requests.utils.quote(title)}"
    if year:
        search_url += f"&y={year}"

    try:
        response = requests.get(search_url, timeout=8)
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "True" and data.get("Search"):
            best = data["Search"][0]  # Top result from fuzzy search
            imdb_id = best.get("imdbID")
            # Now fetch full details by IMDb ID for poster + ratings
            detail_url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}&plot=short"
            detail_resp = requests.get(detail_url, timeout=8)
            detail_resp.raise_for_status()
            detail_data = detail_resp.json()
            if detail_data.get("Response") == "True":
                # Force HTTPS on poster
                if detail_data.get("Poster") and detail_data["Poster"] != "N/A":
                    detail_data["Poster"] = detail_data["Poster"].replace("http://", "https://")
                return detail_data
        print(f"OMDb search found nothing for: {title}")
        return {}
    except Exception as e:
        print(f"Failed to fetch OMDb data: {e}")
        return {}
