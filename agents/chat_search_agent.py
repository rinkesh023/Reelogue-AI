import os
import json
import concurrent.futures
from groq import Groq
from tools.omdb_fetch import fetch_omdb_data

CHAT_SEARCH_SYSTEM = """You are Reelogue's intelligent conversational search agent.
The user will ask you for movies based on an actor, director, theme, or mood (e.g. "movies by Nolan", "sci-fi from the 90s").
Your job is to identify the best 5 movies that match their query.
Return ONLY valid JSON matching this exact structure:
[
  {
    "title": "Movie Title",
    "year": 2023,
    "taste_match": 95,
    "type": "Movie",
    "why_you_will_love_it": "1-2 sentence explanation of why this matches their query"
  }
]
Do not return conversational text, only the array. Keep it to exactly 5 movies."""

def get_chat_search_results(query: str) -> list:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": CHAT_SEARCH_SYSTEM},
                {"role": "user", "content": query}
            ]
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        raw = "[]"

    # Robust JSON extraction for arrays
    start_idx = raw.find("[")
    end_idx = raw.rfind("]")
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        raw = raw[start_idx:end_idx+1]
    else:
        raw = "[]"

    try:
        recs = json.loads(raw)
        
        def assign_poster(r):
            omdb_info = fetch_omdb_data(r.get("title"), str(r.get("year", "")))
            if omdb_info and omdb_info.get("Poster") and omdb_info.get("Poster") != "N/A":
                r["poster_url"] = omdb_info.get("Poster").replace("http://", "https://")
            else:
                r["poster_url"] = "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&q=80"
            return r

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            recs = list(executor.map(assign_poster, recs))
            
        return recs
    except Exception as e:
        return []
