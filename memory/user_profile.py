from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UserProfile:
    """Stores a user's taste profile built during onboarding."""

    name: str = ""
    favourite_genres: list[str] = field(default_factory=list)
    favourite_films: list[str] = field(default_factory=list)
    favourite_directors: list[str] = field(default_factory=list)
    mood: str = ""                        # e.g. "want something light", "need to cry"
    viewing_context: str = ""             # e.g. "solo", "date night", "family"
    content_type: str = "both"            # "movies", "series", "both"
    language_preference: list[str] = field(default_factory=list)
    disliked_genres: list[str] = field(default_factory=list)
    streaming_services: list[str] = field(default_factory=list)
    ratings_history: list[dict] = field(default_factory=list)   # [{title, rating, feedback}]

    def to_prompt_context(self) -> str:
        """Format profile as a context string for Gemini prompts."""
        lines = []
        if self.name:
            lines.append(f"User name: {self.name}")
        if self.favourite_genres:
            lines.append(f"Favourite genres: {', '.join(self.favourite_genres)}")
        if self.favourite_films:
            lines.append(f"Favourite films: {', '.join(self.favourite_films)}")
        if self.favourite_directors:
            lines.append(f"Favourite directors: {', '.join(self.favourite_directors)}")
        if self.mood:
            lines.append(f"Current mood: {self.mood}")
        if self.viewing_context:
            lines.append(f"Viewing context: {self.viewing_context}")
        if self.disliked_genres:
            lines.append(f"Dislikes: {', '.join(self.disliked_genres)}")
        if self.streaming_services:
            lines.append(f"Has access to: {', '.join(self.streaming_services)}")
        if self.content_type != "both":
            lines.append(f"Wants: {self.content_type} only")
        if self.ratings_history:
            recent = self.ratings_history[-5:]
            history_str = "; ".join(
                f"{r['title']} ({r['rating']}/5{': ' + r['feedback'] if r.get('feedback') else ''})"
                for r in recent
            )
            lines.append(f"Recent ratings: {history_str}")
        if self.language_preference:
            lines.append(f"Regional Cinema Priority: MUST prioritize recommendations from -> {', '.join(self.language_preference)}")
        return "\n".join(lines)

    def add_rating(self, title: str, rating: int, feedback: str = ""):
        self.ratings_history.append({"title": title, "rating": rating, "feedback": feedback})
