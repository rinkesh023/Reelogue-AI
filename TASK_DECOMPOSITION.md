# Task Decomposition & System Specification

Reelogue is broken down into modular, agent-driven tasks to ensure scalability and reliability.

## 1. User Profiling & Memory (Onboarding)
- **Task**: Capture user preferences (genres, films, mood, streaming services).
- **Agent**: `Onboarding Agent`.
- **Output**: A structured `UserProfile` object persisted in Supabase/SQLite.

## 2. Multi-Vector Recommendation Generation
- **Task**: Generate 5-10 highly relevant movie picks based on the user's Profile.
- **Agent**: `Recommendation Agent`.
- **Tools**: Groq (Llama 3.1) for rapid reasoning and pattern matching.
- **Goal**: Provide a "match score" for each pick.

## 3. Concurrent Data Aggregation
- **Task**: Fetch metadata, reviews, and streaming info in parallel.
- **Tools**: 
    - `TMDB`: Basic metadata and high-res backdrops.
    - `Fanart.tv`: Premium upscale posters.
    - `Tavily`: Real-time web scraping of critical reviews.
    - `Watchmode`: Streaming availability discovery.

## 4. Review Synthesis (The Critic)
- **Task**: Condense hundreds of data points into a concise, readable review.
- **Agent**: `Review Agent`.
- **Output**: A structured JSON object containing verdict, scores, and streaming info.

## 5. Quality Assurance (LLM-as-Judge)
- **Task**: Audit the synthesized review for accuracy and relevance.
- **Agent**: `Judge Agent` (Gemini 2.5 Flash).
- **Process**: Scores the review against a 5-point rubric and suggests improvements if scores are low.

## 6. Premium Interface Delivery
- **Task**: Render the data in a modern, dark-mode Streamlit dashboard.
- **Features**: Horizontal scrolling, radial progress bars, and animated glassmorphism cards.
