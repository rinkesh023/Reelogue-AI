import os
import requests

FANART_BASE = "http://webservice.fanart.tv/v3/movies"

def get_fanart_poster(tmdb_id: int) -> str | None:
    """Fetch high-quality movie poster from Fanart.tv using TMDB ID."""
    api_key = os.getenv("FANART_TV_API_KEY")
    if not api_key or not tmdb_id:
        return None

    try:
        url = f"{FANART_BASE}/{tmdb_id}?api_key={api_key}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            posters = data.get("movieposter", [])
            if posters:
                # Return the first high-quality poster found
                return posters[0].get("url")
    except Exception as e:
        print(f"Fanart.tv fetch failed for {tmdb_id}: {e}")
    
    return None
