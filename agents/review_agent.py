import os
import json
import concurrent.futures
from groq import Groq
from tools.tavily_search import fetch_reviews, fetch_streaming_availability
from tools.tmdb_fetch import get_movie_full
from tools.omdb_fetch import fetch_omdb_data
from tools.watchmode_fetch import get_watchmode_streaming_sources
from memory.user_profile import UserProfile

REVIEW_SYNTHESIS_SYSTEM = """You are Reelogue's expert review synthesiser — a deeply analytical and knowledgeable film critic friend.

Read the raw review data and produce a structured JSON analysis.
DO NOT provide minimal one-liners. Provide detailed, expressive, and substantial 3-4 sentence paragraphs that truly capture the film's essence, critical nuances, and real web-based audience reception.

Return ONLY valid JSON:

{
  "verdict": "3-4 punchy, evocative sentences providing a definitive and highly detailed final verdict. Dive into what makes it special.",
  "summary": "At least 4-5 sentences synthesising the plot and the overarching reaction. Be specific about the cinematography, acting, or directing.",
  "scores": {
    "imdb": "7.8/10",
    "rotten_tomatoes_critics": "94%",
    "rotten_tomatoes_audience": "88%",
    "metacritic": "82/100",
    "letterboxd": "4.1/5"
  },
  "critic_consensus": "A substantial 3-sentence summary of what professional critics universally praised or heavily criticised. Be highly specific.",
  "audience_take": "A substantial 3-sentence summary of how general web audiences feel vs critics. Mention real points of enjoyment or boredom.",
  "best_for": "Be specific (e.g. 'Fans of slow-burn, psychological A24-style thrillers who love deep character studies')",
  "avoid_if": "Be specific (e.g. 'Viewers looking for rapid-action or those who hate ambiguous endings')",
  "taste_match_note": "A deeply personalised 2-sentence note about why this matches (or completely misses) the user's taste preferences.",
  "reelogue_rating": 8.4
}

Important Rules:
1. reelogue_rating is your own weighted score (0.0-10.0). Not every film is a 9/10. Use decimal precision.
2. If data is missing for a score, fill it with 'N/A'.
3. Your text MUST be high effort, cinematic, and detailed. Do NOT be lazy."""

def review_movie(title: str, year: str, profile: UserProfile) -> dict:
    print(f"  [1-3/4] Parallel processing APIs (TMDB, OMDb, Tavily, Watchmode)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        f_metadata = executor.submit(get_movie_full, title, year)
        f_omdb = executor.submit(fetch_omdb_data, title, year)
        f_reviews = executor.submit(fetch_reviews, title, year)
        f_streaming = executor.submit(fetch_streaming_availability, title, year)
        f_watchmode = executor.submit(get_watchmode_streaming_sources, title, year)

        metadata = f_metadata.result()
        omdb_data = f_omdb.result()
        raw_reviews = f_reviews.result()
        streaming = f_streaming.result()
        watchmode_sources = f_watchmode.result()

    print(f"  [4/4] Synthesising with Groq...")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    review_context = f"""Movie: {title} ({year})

User profile context:
{profile.to_prompt_context()}

Raw review data from Tavily searches:
IMDb data:
{raw_reviews.get('imdb', {}).get('answer', 'Not found')}
{chr(10).join(raw_reviews.get('imdb', {}).get('snippets', []))}

Rotten Tomatoes data:
{raw_reviews.get('rotten_tomatoes', {}).get('answer', 'Not found')}
{chr(10).join(raw_reviews.get('rotten_tomatoes', {}).get('snippets', []))}

Metacritic data:
{raw_reviews.get('metacritic', {}).get('answer', 'Not found')}
{chr(10).join(raw_reviews.get('metacritic', {}).get('snippets', []))}

Letterboxd data:
{raw_reviews.get('letterboxd', {}).get('answer', 'Not found')}
{chr(10).join(raw_reviews.get('letterboxd', {}).get('snippets', []))}

OMDb Ratings Data:
{json.dumps(omdb_data.get('Ratings', []), indent=2)}
IMDb Rating (from OMDb): {omdb_data.get('imdbRating', 'N/A')} with {omdb_data.get('imdbVotes', 'N/A')} votes.

Streaming availability (from Tavily):
{streaming.get('answer', 'Not found')}

Streaming availability (from Watchmode API):
{', '.join([s.get('name') for s in watchmode_sources]) if watchmode_sources else 'Not found'}

Synthesise this into the required JSON format."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": REVIEW_SYNTHESIS_SYSTEM},
                {"role": "user", "content": review_context}
            ],
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        raw = json.dumps({"verdict": f"GROQ API ERROR: {str(e)}", "summary": "API Call Failed"})

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    try:
        synthesis = json.loads(raw)
    except json.JSONDecodeError:
        synthesis = {
            "verdict": "Review data could not be fully parsed.",
            "summary": raw[:500],
            "scores": {},
            "reelogue_rating": None,
        }

    if metadata:
        final_metadata = metadata
    else:
        final_metadata = {
            "title": omdb_data.get("Title", title),
            "release_year": omdb_data.get("Year", year),
            "director": omdb_data.get("Director"),
            "genres": [g.strip() for g in omdb_data.get("Genre", "").split(",")] if omdb_data.get("Genre") else []
        }
        
    if not final_metadata.get("poster_url") and omdb_data.get("Poster") and omdb_data.get("Poster") != "N/A":
        final_metadata["poster_url"] = omdb_data.get("Poster").replace("http://", "https://")

    return {
        "metadata": final_metadata,
        "synthesis": synthesis,
        "streaming_raw": streaming.get("answer", ""),
        "raw_sources": {
            source: data.get("urls", [])
            for source, data in raw_reviews.items()
        },
    }
