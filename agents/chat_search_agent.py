import os
import json
import concurrent.futures
from groq import Groq
from tools.omdb_fetch import fetch_omdb_data

CHAT_SEARCH_SYSTEM = """You are Reelogue's intelligent conversational movie discovery agent.
For ANY user query — whether it's a movie title, actor, director, genre, or mood — you MUST:
1. If the user gives a movie title (e.g. "RRR", "Dangal"): Return that movie PLUS 4 highly similar movies.
2. If the user gives an actor/director (e.g. "Christopher Nolan"): Return their 5 most popular works.
3. If the user gives a theme/mood: Return the 5 best matches.

ALWAYS return EXACTLY 5 entries. NEVER return prose, explanations, or markdown. Return ONLY this exact JSON array:
[
  {
    "title": "Movie Title",
    "year": 2023,
    "taste_match": 95,
    "type": "Movie",
    "why_you_will_love_it": "1-2 sentence explanation of why this matches their query"
  }
]"""

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

    # Robust JSON extraction for arrays or single objects
    start_idx_array = raw.find("[")
    end_idx_array = raw.rfind("]")
    
    start_idx_obj = raw.find("{")
    end_idx_obj = raw.rfind("}")
    
    if start_idx_array != -1 and end_idx_array != -1 and end_idx_array > start_idx_array:
        raw = raw[start_idx_array:end_idx_array+1]
    elif start_idx_obj != -1 and end_idx_obj != -1 and end_idx_obj > start_idx_obj:
        # Groq returned a single dictionary instead of an array. Wrap it in a list!
        raw = "[" + raw[start_idx_obj:end_idx_obj+1] + "]"
    else:
        raw = "[]"

    try:
        recs = json.loads(raw)
        
        def assign_poster(r):
            from tools.image_fetcher import get_best_poster
            r["poster_url"] = get_best_poster(r.get("title", ""), str(r.get("year", "")))
            return r

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            recs = list(executor.map(assign_poster, recs))
            
        return recs
    except Exception as e:
        return []
