# Task Decomposition & System Specification: Reelogue AI

The Reelogue system is architected into five distinct task modules, each managed by a specialized agentic workflow.

## Module 1: Persistent Onboarding & Memory
- **Objective**: Construct a dynamic "Taste Profile" for the user.
- **Sub-tasks**:
    - Capture preferred genres, favorite/disliked films, and current mood.
    - Persist profile data via Supabase (Cloud) or SQLite (Local).
    - Generate a unique Session ID for cross-device synchronization.

## Module 2: Recommendation Orchestration
- **Objective**: Generate 10 high-relevance candidates.
- **Sub-tasks**:
    - Query LLM (Groq Llama 3.1) with the user's Profile context.
    - Calculate a "Match Score" (%) based on profile overlap.
    - Output structured JSON to avoid parsing errors.

## Module 3: Parallel Data Fetching (The Toolset)
- **Objective**: Aggregate metadata and high-res assets concurrently.
- **Sub-tasks**:
    - **TMDB & Fanart.tv**: Fetch high-resolution posters and basic metadata.
    - **Tavily Search**: Scrape the web for critical consensus and specific review scores.
    - **Watchmode**: Execute a global lookup for streaming availability.
    - **Concurrency**: Use a ThreadPool (10 workers) to execute all fetches at once.

## Module 4: Synthesis & Verdict Generation
- **Objective**: Turn raw data into a human-readable high-quality review.
- **Sub-tasks**:
    - Summarize multi-domain critical data (IMDb, RT, Metacritic).
    - Map streaming locations to the user's specific subscriptions.
    - Provide "Best For" and "Avoid If" logic for quick decision-making.

## Module 5: Verification (LLM-as-Judge)
- **Objective**: Perform a rigorous quality audit.
- **Sub-tasks**:
    - An independent agent (Gemini 2.5 Flash) audits the synthesis results.
    - Evaluate across 5 key rubric points: Accuracy, Relevance, Synthesis Quality, Source Coverage, and Personalization.
    - Block or flag outputs that fail to meet high-reliability standards.
