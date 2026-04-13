import os
import json
from groq import Groq
from tools.tavily_search import fetch_reviews
from memory.user_profile import UserProfile
from agents.review_agent import review_movie

SEARCH_SYSTEM_PROMPT = """You are an Agentic Search Assistant.
Your goal is to extract the absolute best movie/series title and year from the user's query and the search results context.
CRITICAL INSTRUCTION: If there are multiple movies with the same name, or if the user's query is ambiguous, you must ALWAYS select the absolute newest/latest movie released (e.g. 2024 overrides 1989). 

Return valid JSON:
{
  "title": "Movie Title",
  "year": "YYYY"
}
If year is unknown, put an empty string. Keep it strictly JSON.
"""

def agentic_search_loop(query: str, profile: UserProfile) -> dict:
    tavily_results = fetch_reviews(query, "")
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    prompt = f"""User Query: {query}
Tavily Search Context: {json.dumps(tavily_results)[:2000]}
Extract the specific title and year in JSON."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        raw = json.dumps({"title": f"GROQ SEARCH ERROR: {str(e)}", "year": ""})

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    try:
        ext = json.loads(raw)
        t_title = ext.get('title', query)
        t_year = str(ext.get('year', ""))
    except Exception as e:
        t_title = query
        t_year = ""

    return review_movie(t_title, t_year, profile)
