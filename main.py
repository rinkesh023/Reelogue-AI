"""
Reelogue — AI-powered movie & series review agent
Powered by Gemini + Tavily + TMDB
"""

import os
from dotenv import load_dotenv
load_dotenv()

from agents.onboarding_agent import run_onboarding
from agents.recommendation_agent import get_recommendations
from agents.review_agent import review_movie
from memory.user_profile import UserProfile


def display_review(review: dict):
    """Pretty-print a full review card to the terminal."""
    meta = review.get("metadata", {})
    syn = review.get("synthesis", {})

    print("\n" + "━"*60)
    print(f"  {meta.get('title', 'Unknown').upper()}  ({meta.get('release_year', '')})")
    if meta.get("director"):
        print(f"  Directed by {meta.get('director')}")
    if meta.get("genres"):
        print(f"  {' · '.join(meta.get('genres', []))}")
    print("━"*60)

    if syn.get("verdict"):
        print(f"\n  \"{syn['verdict']}\"\n")

    rating = syn.get("reelogue_rating")
    if rating:
        stars = "★" * int(rating/2) + ("½" if rating % 2 >= 1 else "") + "☆" * (5 - int(rating/2) - (1 if rating % 2 >= 1 else 0))
        print(f"  Reelogue Rating: {rating}/10  {stars}")

    scores = syn.get("scores", {})
    if scores:
        print("\n  Review scores:")
        labels = {
            "imdb": "IMDb",
            "rotten_tomatoes_critics": "RT Critics",
            "rotten_tomatoes_audience": "RT Audience",
            "metacritic": "Metacritic",
            "letterboxd": "Letterboxd",
        }
        for key, label in labels.items():
            val = scores.get(key, "N/A")
            if val and val != "N/A":
                print(f"    {label:<20} {val}")

    if syn.get("summary"):
        print(f"\n  Summary:\n  {syn['summary']}")

    if syn.get("critic_consensus"):
        print(f"\n  Critics say: {syn['critic_consensus']}")

    if syn.get("audience_take"):
        print(f"  Audiences say: {syn['audience_take']}")

    if syn.get("best_for"):
        print(f"\n  Best for: {syn['best_for']}")

    if syn.get("avoid_if"):
        print(f"  Skip if: {syn['avoid_if']}")

    if syn.get("taste_match_note"):
        print(f"\n  For you: {syn['taste_match_note']}")

    if review.get("streaming_raw"):
        print(f"\n  Where to watch: {review['streaming_raw'][:200]}")

    if meta.get("poster_url"):
        print(f"\n  Poster: {meta['poster_url']}")

    if meta.get("trailer_key"):
        print(f"  Trailer: https://youtube.com/watch?v={meta['trailer_key']}")

    print("\n" + "━"*60 + "\n")


def display_recommendations(recs: list[dict]):
    """Display recommendation cards."""
    print("\n" + "="*60)
    print("  YOUR PERSONALISED PICKS")
    print("="*60)
    for i, rec in enumerate(recs, 1):
        match = rec.get("taste_match", 0)
        bar = "█" * (match // 10) + "░" * (10 - match // 10)
        print(f"\n  {i}. {rec['title']} ({rec.get('year', '')}) [{rec.get('type','movie').upper()}]")
        print(f"     Taste match: {bar} {match}%")
        print(f"     {rec.get('reason', '')}")
    print()


def get_user_choice(recs: list[dict]) -> tuple[str, str] | None:
    """Let user pick a recommendation to review."""
    print("Which would you like to review in detail?")
    print("  Enter a number (1-5), type a custom title, or 'quit' to exit\n")
    choice = input("  > ").strip()

    if choice.lower() == "quit":
        return None

    if choice.isdigit() and 1 <= int(choice) <= len(recs):
        rec = recs[int(choice) - 1]
        return rec["title"], rec.get("year", "")

    return choice, ""


def main():
    print("""
██████╗ ███████╗███████╗██╗      ██████╗  ██████╗ ██╗   ██╗███████╗
██╔══██╗██╔════╝██╔════╝██║     ██╔═══██╗██╔════╝ ██║   ██║██╔════╝
██████╔╝█████╗  █████╗  ██║     ██║   ██║██║  ███╗██║   ██║█████╗  
██╔══██╗██╔══╝  ██╔══╝  ██║     ██║   ██║██║   ██║██║   ██║██╔══╝  
██║  ██║███████╗███████╗███████╗╚██████╔╝╚██████╔╝╚██████╔╝███████╗
╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝
         Your AI-powered cinema companion
    """)

    # Step 1: Onboarding
    profile = run_onboarding()

    while True:
        # Step 2: Get recommendations
        print("Generating your personalised picks...\n")
        recs = get_recommendations(profile)

        if not recs:
            print("Could not generate recommendations. Please check your API keys.")
            break

        display_recommendations(recs)

        # Step 3: User picks one to review
        choice = get_user_choice(recs)
        if choice is None:
            print("\nThanks for using Reelogue. Lights out!\n")
            break

        title, year = choice

        print(f"\nFetching full review for '{title}'...\n")
        review = review_movie(title, year, profile)
        display_review(review)

        # Step 4: Collect feedback to improve profile
        print("How would you rate this recommendation? (1-5, or press Enter to skip)")
        rating_input = input("  > ").strip()
        if rating_input.isdigit() and 1 <= int(rating_input) <= 5:
            feedback = input("  Any comment? (optional): ").strip()
            profile.add_rating(title, int(rating_input), feedback)
            print("  Thanks! Your taste profile has been updated.\n")

        # Step 5: Continue or quit
        again = input("Get more recommendations? (y/n): ").strip().lower()
        if again != "y":
            print("\nThanks for using Reelogue. Lights out!\n")
            break


if __name__ == "__main__":
    main()
