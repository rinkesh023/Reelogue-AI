# Problem Statement: The Paradox of Choice in Modern Cinema

## The Problem
In the era of streaming abundance, movie enthusiasts face a "paradox of choice." While thousands of titles are available at the click of a button, finding a film that truly matches a user's unique, nuanced taste has become increasingly difficult.

Existing solutions suffer from several key issues:
1.  **Fragmented Data**: Review scores are scattered across IMDb, Rotten Tomatoes, Metacritic, and Letterboxd. Users must manually jump between sites to get a full picture.
2.  **Generic Recommendations**: Most algorithms use simple collaborative filtering (e.g., "Users who liked X also liked Y"), which fails to capture the specific "vibe" or "mood" a user is looking for.
3.  **Review Overload**: Reading dozens of reviews to find a consensus is time-consuming.
4.  **Low Discovery Reliability**: AI-generated recommendations often lack a "verification" layer, leading to generic or irrelevant suggestions.

## The Solution: Reelogue
Reelogue solves this by behaving as a **fully agentic cinema companion**. It doesn't just search; it **thinks, synthesizes, and audits**.

By leveraging a multi-agent architecture, Reelogue:
-   Aggregates data from multiple sources (TMDB, OMDb, Tavily search) concurrently.
-   Synthesizes mass review data into a single, cohesive "verdict."
-   Employs an independent **Judge Agent** (LLM-as-Judge) to audit the quality and relevance of its own recommendations against the user's profile.
-   Provides a high-fidelity UI that makes the discovery process as premium as the cinema itself.
