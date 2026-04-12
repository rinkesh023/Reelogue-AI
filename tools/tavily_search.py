import os
from tavily import TavilyClient


def fetch_reviews(movie_title: str, year: str = "") -> dict:
    """
    Use Tavily to search live review sites for a movie.
    Returns structured review data from multiple sources.
    """
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    query_title = f"{movie_title} {year}".strip()

    sources = {
        "imdb": f"{query_title} IMDb rating score review",
        "rotten_tomatoes": f"{query_title} Rotten Tomatoes tomatometer audience score",
        "metacritic": f"{query_title} Metacritic score critic reviews",
        "letterboxd": f"{query_title} Letterboxd average rating",
    }

    reviews = {}

    for source, query in sources.items():
        try:
            result = client.search(
                query=query,
                search_depth="basic",
                max_results=2,
                include_answer=True,
            )
            reviews[source] = {
                "answer": result.get("answer", ""),
                "snippets": [r.get("content", "")[:300] for r in result.get("results", [])[:2]],
                "urls": [r.get("url", "") for r in result.get("results", [])[:2]],
            }
        except Exception as e:
            reviews[source] = {"answer": "", "snippets": [], "urls": [], "error": str(e)}

    return reviews


def fetch_streaming_availability(movie_title: str, year: str = "") -> dict:
    """Search for where a movie is currently streaming."""
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    query = f"Where to watch {movie_title} {year} streaming Netflix Amazon Disney Plus HBO"

    try:
        result = client.search(
            query=query,
            search_depth="basic",
            max_results=3,
            include_answer=True,
        )
        return {
            "answer": result.get("answer", ""),
            "snippets": [r.get("content", "")[:300] for r in result.get("results", [])[:3]],
        }
    except Exception as e:
        return {"answer": "", "snippets": [], "error": str(e)}
