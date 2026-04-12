import os
import requests
from dotenv import load_dotenv

load_dotenv()
WATCHMODE_API_KEY = os.getenv("WATCHMODE_API_KEY")

def get_watchmode_streaming_sources(title: str, year: str = "") -> list:
    """
    Fetch streaming sources from Watchmode API.
    Requires first searching for the title ID, then getting its sources.
    """
    if not WATCHMODE_API_KEY:
        print("Warning: WATCHMODE_API_KEY is not set.")
        return []
    
    # 1. Search for title ID
    search_url = f"https://api.watchmode.com/v1/search/?apiKey={WATCHMODE_API_KEY}&search_field=name&search_value={title}"
    try:
        search_res = requests.get(search_url)
        search_res.raise_for_status()
        search_data = search_res.json()
        
        matches = search_data.get("title_results", [])
        if not matches:
            return []
            
        # Try to match the year if provided
        best_match = matches[0]
        if year:
            for match in matches:
                if str(match.get("year")) == str(year):
                    best_match = match
                    break
                    
        title_id = best_match["id"]
        
        # 2. Get title streaming details using ID
        sources_url = f"https://api.watchmode.com/v1/title/{title_id}/sources/?apiKey={WATCHMODE_API_KEY}"
        sources_res = requests.get(sources_url)
        sources_res.raise_for_status()
        sources_data = sources_res.json()
        
        # Deduplicate sources (Watchmode returns multiple entries for SD, HD, 4K)
        unique_sources = {}
        for source in sources_data:
            name = source.get("name")
            if name and name not in unique_sources:
                unique_sources[name] = source
                
        return list(unique_sources.values())
        
    except Exception as e:
        print(f"Failed to fetch Watchmode data: {e}")
        return []
