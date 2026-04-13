import os
import json
import google.generativeai as genai
from tools.tavily_search import fetch_reviews
from tools.tmdb_fetch import get_movie_full
from memory.user_profile import UserProfile
from agents.review_agent import review_movie

SEARCH_SYSTEM_PROMPT = """You are an Agentic Search Assistant.
Your goal is to extract the movie/series title from the user's query and use the provided tools to fetch its reviews.
When asked to find and analyze a film:
1. Call the `tavily_search_tool` with the query string to discover current trends or reviews.
2. Based on the tool's response, produce a final JSON containing the extracted 'title' and 'year'.

Return valid JSON:
{
  "title": "Movie Title",
  "year": "YYYY"
}
If year is unknown, put an empty string. Keep it strictly JSON.
"""

def tavily_search_tool(query: str) -> dict:
    """Search the public web for current fashion trends or movie reviews."""
    return fetch_reviews(query, "")

def agentic_search_loop(query: str, profile: UserProfile) -> dict:
    """
    Implements an agentic loop where the model can call tools autonomously.
    """
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Passing the python function as a tool to the model
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SEARCH_SYSTEM_PROMPT,
        tools=[tavily_search_tool]
    )

    chat = model.start_chat(enable_automatic_function_calling=True)
    response = chat.send_message(query)
    
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()
    
    try:
        ext = json.loads(raw)
        t_title = ext.get('title', query)
        t_year = ext.get('year', "")
    except Exception as e:
        t_title = query
        t_year = ""

    # Once we have the data, hand off to the dedicated review agent to synthesize
    return review_movie(t_title, t_year, profile)
