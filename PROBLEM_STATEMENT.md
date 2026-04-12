# Problem Statement: Reelogue

## The Problem
Movie discovery is broken — users spend more time choosing than watching. Review scores are scattered across IMDb, Rotten Tomatoes, Metacritic, and Letterboxd with no unified view. Furthermore, recommendations from streaming platforms are purely engagement-driven, meaning they are designed to push trending content rather than serving meaningful selections that are genuinely taste-matched to the individual user.

## The User
Our target audience consists of film enthusiasts (cinephiles) who want meaningful recommendations aligned to their actual taste, not just what's trending or mathematically optimized for algorithmic watch-time.

## Why Agentic
Traditional linear programming or a single-shot prompt approach falls completely short for this problem because each step requires fundamentally different capabilities:
- Conversational profiling requires LLM dialogue capabilities.
- Personalized reasoning requires an LLM reasoning over structured taste data.
- Live web search requires specialized parallel tooling to scrape data across multiple review sites (Tavily).
- Structured synthesis requires an LLM to unify raw data and produce clean formatting.
A single prompt cannot handle this complexity effectively. An agentic pipeline where each agent independently owns its step is the correct architecture to produce robust and highly personalized outputs.

## The Solution
**Reelogue** is a multi-step AI agent application that:
1. Builds a taste profile through conversation
2. Recommends films matched to that profile
3. Aggregates live review scores from all major platforms via Tavily search
4. Synthesises a unified review using Gemini
5. Evaluates its own output quality via an LLM-as-Judge verification step
