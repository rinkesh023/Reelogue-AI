import os
import json
from groq import Groq
from memory.user_profile import UserProfile
from tools.omdb_fetch import fetch_omdb_data

RECOMMENDATION_SYSTEM = """You are Reelogue's expert curation AI.
Given the User's Taste Profile, generate exactly 10 highly personalised movie/series recommendations.
Return ONLY valid JSON matching this exact structure:
[
  {
    "title": "Movie Title",
    "year": 2023,
    "taste_match": 95,
    "type": "Movie",
    "why_you_will_love_it": "1-2 sentence explanation tailored strictly to their profile"
  }
]
"""

def get_recommendations(profile: UserProfile) -> list:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""User taste profile:
{profile.to_prompt_context()}

Suggest 10 personalised recommendations as JSON."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": RECOMMENDATION_SYSTEM},
                {"role": "user", "content": prompt}
            ]
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        raw = "[]"

    # Robust JSON extraction for arrays to handle conversational prose
    start_idx = raw.find("[")
    end_idx = raw.rfind("]")
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        raw = raw[start_idx:end_idx+1]
    else:
        raw = "[]"

    try:
        recs = json.loads(raw)
        import concurrent.futures
        
        def assign_poster(r):
            from tools.image_fetcher import get_best_poster
            r["poster_url"] = get_best_poster(r.get("title"), str(r.get("year", "")))
            return r

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            recs = list(executor.map(assign_poster, recs))
            
        return recs
    except Exception as e:
        return []
