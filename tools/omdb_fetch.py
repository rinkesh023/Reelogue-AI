import os
import requests
from dotenv import load_dotenv

load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

def fetch_omdb_data(title: str, year: str = "") -> dict:
    """
    Fetch movie metadata from OMDb API.
    """
    if not OMDB_API_KEY:
        print("Warning: OMDB_API_KEY is not set.")
        return {}
        
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}"
    if year:
        url += f"&y={year}"
        
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "True":
            return data
        else:
            print(f"OMDb Error: {data.get('Error')}")
            return {}
    except Exception as e:
        print(f"Failed to fetch OMDb data: {e}")
        return {}
