import os
import json
import concurrent.futures
import google.generativeai as genai
from tools.tavily_search import fetch_reviews, fetch_streaming_availability
from tools.tmdb_fetch import get_movie_full
from tools.omdb_fetch import fetch_omdb_data
from tools.watchmode_fetch import get_watchmode_streaming_sources
from memory.user_profile import UserProfile

REVIEW_SYNTHESIS_SYSTEM = """You are Reelogue's expert review synthesiser — like a knowledgeable film critic friend.

Given raw review data scraped from multiple sources, produce a structured JSON analysis.
Return ONLY valid JSON, no other text:

{
  "verdict": "One punchy sentence verdict (e.g. 'A masterclass in tension that demands a big screen')",
  "summary": "3-4 sentences synthesising what critics and audiences agree/disagree on",
  "scores": {
    "imdb": "7.8/10",
    "rotten_tomatoes_critics": "94%",
    "rotten_tomatoes_audience": "88%",
    "metacritic": "82/100",
    "letterboxd": "4.1/5"
  },
  "critic_consensus": "What critics universally praise or criticise",
  "audience_take": "How general audiences feel vs critics",
  "best_for": "Who will love this film (e.g. 'fans of slow-burn psychological thrillers')",
  "avoid_if": "Who should skip it",
  "taste_match_note": "Personalised note about why this matches (or doesn't) the user's taste",
  "reelogue_rating": 8.4
}

reelogue_rating is your own weighted score (0-10) considering all sources.
Be honest — not every film is a 9/10. Use decimal precision.
Fill scores with 'N/A' if data was not found."""

REVIEW_SYSTEM_FALLBACK = """If review data is sparse, still produce the full JSON.
Use 'N/A' for missing scores and note the data gap in the summary."""


def review_movie(title: str, year: str, profile: UserProfile) -> dict:
    """
    Full review pipeline:
    1. Fetch metadata from TMDB
    2. Fetch live reviews from all sources via Tavily  
    3. Fetch streaming availability via Tavily
    4. Synthesise everything with Gemini
    Returns a complete review dict ready for display.
    """

    print(f"  [1-3/4] Parallel processing APIs (TMDB, OMDb, Tavily, Watchmode)...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        f_metadata = executor.submit(get_movie_full, title)
        f_omdb = executor.submit(fetch_omdb_data, title, year)
        f_reviews = executor.submit(fetch_reviews, title, year)
        f_streaming = executor.submit(fetch_streaming_availability, title, year)
        f_watchmode = executor.submit(get_watchmode_streaming_sources, title, year)

        metadata = f_metadata.result()
        omdb_data = f_omdb.result()
        raw_reviews = f_reviews.result()
        streaming = f_streaming.result()
        watchmode_sources = f_watchmode.result()

    print(f"  [4/4] Synthesising with Gemini...")
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        system_instruction=REVIEW_SYNTHESIS_SYSTEM,
    )

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

    response = model.generate_content(review_context)
    raw = response.text.strip()

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
        
    # Fallback to OMDb poster if TMDB failed/rejected
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
