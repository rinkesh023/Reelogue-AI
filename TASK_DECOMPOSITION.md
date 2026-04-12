# Task Decomposition

Reelogue delegates massive processing pipelines across four specialized AI agents. This task breakdown highlights what each agent is responsible for.

## Agent Breakdown

| Agent | Input | Output | Tools | Decision Points | Failure Handling |
| --- | --- | --- | --- | --- | --- |
| **Agent 1: Onboarding Agent** | User conversation turns | UserProfile JSON | Gemini chat | Decides when enough info is collected (triggers PROFILE_COMPLETE JSON) | Defaults applied for missing fields |
| **Agent 2: Recommendation Agent** | UserProfile | List of 5 dicts (title, year, type, reason, taste_match %) | Gemini text generation | Genre/mood/context weighting | JSON parse fallback (returns empty list or default values) |
| **Agent 3: Review Agent** | Title + Year + UserProfile | Metadata + Synthesis dict | TMDB API (metadata/posters), Tavily Search x4 (IMDb/RT/Metacritic/Letterboxd), OMDB API (scores), Watchmode API (streaming), Gemini synthesis | Decides which sources returned usable data vs. failed scrapes | Marks 'N/A' for missing review scores |
| **Agent 4: Judge Agent** | Complete review output + UserProfile | Rubric scores JSON | Gemini (separate call) | Independent per-criterion scoring | Default score of 1 with error note if JSON formatting fails |

## Data Flow Between Agents
1. The **Onboarding Agent** captures the user dialogue to populate the unified `UserProfile` object. 
2. The populated `UserProfile` flows into the **Recommendation Agent** to provide hyper-personalized outputs (5 movie picks).
3. Upon selecting one film from the recommendations, the title and year, as well as the `UserProfile` data, are routed into the **Review Agent**, which handles parallel tool invocations.
4. The output payload generated from the **Review Agent** represents the final context and paired with the `UserProfile`, it is passed directly to the **Judge Agent** which evaluates the AI reasoning quality and formats a JSON rubric scores report.

## Agentic Loop Pattern
The Review Agent explicitly leverages a parallel tool execution loop pattern. Rather than forcing the LLM to manage serial tool requests step by step, the Review agent utilizes Python `concurrent.futures` to trigger independent retrieval threads (TMDB, OMDB, Tavily x4, Watchmode). Once all threads complete, the LLM maps all concurrent raw data to execute the synthesis loop.
