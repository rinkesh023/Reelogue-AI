import os
import json
import google.generativeai as genai
from memory.user_profile import UserProfile
from tools.omdb_fetch import fetch_omdb_data

RECOMMENDATION_SYSTEM = """You are Reelogue's recommendation engine. Given a user taste profile, 
suggest exactly 10 films or series that are a strong match.

Return ONLY a valid JSON array, no other text:
[
  {
    "title": "Exact film title",
    "year": "2024",
    "type": "movie",
    "reason": "2-sentence personalised reason referencing their specific tastes",
    "taste_match": 92
  }
]

Rules:
- taste_match is 0-100, be honest (don't give everything 95+)
- reason must directly reference something from their profile (e.g. "Since you loved Parasite's class tension...")
- Mix well-known and hidden gems
- Respect disliked genres strictly
- If they want series, suggest series. If movies, suggest movies. If both, mix.
- Prioritise titles likely available on their streaming services"""


def get_recommendations(profile: UserProfile) -> list[dict]:
    """Generate personalised recommendations using Gemini."""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=RECOMMENDATION_SYSTEM,
    )

    prompt = f"""User taste profile:
{profile.to_prompt_context()}

Suggest 10 personalised recommendations as JSON."""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    try:
        recs = json.loads(raw)
        import concurrent.futures
        
        def assign_poster(r):
            omdb_info = fetch_omdb_data(r.get("title"), str(r.get("year", "")))
            if omdb_info and omdb_info.get("Poster") and omdb_info.get("Poster") != "N/A":
                r["poster_url"] = omdb_info.get("Poster").replace("http://", "https://")
            else:
                r["poster_url"] = "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&q=80"
            return r

        with concurrent.futures.ThreadPoolExecutor() as executor:
            recs = list(executor.map(assign_poster, recs))
            
        return recs
    except Exception as e:
        # Fallback: return empty list if parsing fails
        print(f"[Warning] Could not parse recommendations JSON: {e}")
        return []
