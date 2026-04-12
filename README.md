# Reelogue
> Your AI-powered cinema companion

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-8E75B2?style=flat-square&logo=googlegemini&logoColor=white)
![Tavily](https://img.shields.io/badge/Tavily-4285F4?style=flat-square&logo=google&logoColor=white)
![TMDB](https://img.shields.io/badge/TMDB-01B4E4?style=flat-square&logo=themoviedatabase&logoColor=white)

Reelogue is a fully agentic application that acts as your personalized film critic and companion. By using conversational memory, massive-scale parallel searching, and LLM-as-judge self-correction, Reelogue curates and verifies the best cinema picks mapped directly to your specific tastes.

## Features
- **Personalised taste profiling:** Automatically translates user context into a reusable profile object.
- **AI recommendations with match scores:** Provides exact film match values based on your preferences.
- **Live review aggregation:** Gathers critical context concurrently across IMDb, Rotten Tomatoes, Metacritic, and Letterboxd.
- **AI-synthesised verdict:** Rewrites overwhelming amounts of reviews into clean, readable judgements.
- **LLM-as-Judge quality evaluation:** Self-checks AI verdicts against a 5-point rigorous rubric.
- **Streaming availability lookup:** Detects where the film can be currently watched.
- **Movie poster display:** Connects metadata pipelines to fetch stunning poster visuals.

## Tech Stack

| Component | Tool / Tech | Purpose |
| --- | --- | --- |
| **Language** | Python | Primary backend scripting. |
| **UI** | Streamlit | Rapid interactive browser frontend prototyping. |
| **AI Brain** | Gemini | Primary LLM orchestrator executing logic and formatting. |
| **Search** | Tavily | Real-time scraper fetching web reviews across designated platforms. |
| **Movie Data** | TMDB | Metadata engine for basic film facts and posters. |
| **Review Data** | OMDb | Fast baseline score fallback and API metrics. |
| **Streaming** | Watchmode API | Reliable lookup for streaming platforms globally. |
| **Deployment**| Streamlit Cloud / Railway | Scalable hosting options for demo delivery. |

## Architecture

```text
       [ User Profile / Form Inputs ]
                  |
                  v
+------------------------------------+
| 1. Onboarding Agent (Gemini Chat)  |
+------------------------------------+
                  | (Generates UserProfile)
                  v
+------------------------------------+
| 2. Recommendation Agent (Gemini)   |
+------------------------------------+
                  | (Outputs 5 Picks)
                  v
+------------------------------------+
| 3. Review Agent (Gemini Synthesis) |
|  -> Parallel Tools: TMDB, OMDb     |
|  -> Parallel Tools: Tavily, Watch  |
+------------------------------------+
                  | (Produces Full Review)
                  v
+------------------------------------+
| 4. Judge Agent (LLM-as-Judge)      |
+------------------------------------+
```

## Project Structure
```
.
├── .env.example
├── .gitignore
├── PROBLEM_STATEMENT.md
├── README.md
├── TASK_DECOMPOSITION.md
├── agents/
│   ├── __init__.py
│   ├── judge_agent.py
│   ├── onboarding_agent.py
│   ├── recommendation_agent.py
│   └── review_agent.py
├── api.py
├── check_models.py
├── frontend/
├── main.py
├── memory/
│   ├── __init__.py
│   └── user_profile.py
├── requirements.txt
├── streamlit_app.py
├── static/
└── tools/
    ├── __init__.py
    ├── omdb_fetch.py
    ├── tavily_search.py
    ├── tmdb_fetch.py
    └── watchmode_fetch.py
```

## Setup Instructions

1. **Clone the repo:**
   ```bash
   git clone https://github.com/yourusername/reelogue.git
   cd reelogue
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment:**
   Copy the example environment variables to a live `.env` file:
   ```bash
   cp .env.example .env
   ```
   *Fill the `.env` with your active keys based on the API list below.*
4. **Run the Application:**
   ```bash
   streamlit run streamlit_app.py
   ```

## API Keys

| Key | Where to Get It | Free Tier Limits |
| --- | --- | --- |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) | 15 RPM / 1M TPM |
| `TAVILY_API_KEY` | [Tavily Dashboard](https://tavily.com/) | 1,000 requests/month |
| `TMDB_API_KEY` | [TMDB Developer](https://developer.themoviedb.org/) | 50 requests/sec |
| `OMDB_API_KEY` | [OMDb API](http://www.omdbapi.com/apikey.aspx) | 1,000 requests/day |
| `WATCHMODE_API_KEY` | [Watchmode Settings](https://v2.watchmode.com/settings/) | 1,000 requests/month |

## How It Works

1. **Step 1: Your Taste Profile:** Users fill in their profile constraints, favorites, and disliked genres dynamically mapping into an active `UserProfile` object over the session.
2. **Step 2: Get My Picks:** The Recommendation Agent runs an AI analysis outputting five exact matches with personalized reasons.
3. **Step 3: Choose a film:** The user selects a specific result, activating a deeper context load.
4. **Step 4: Display the full review:** Parallel APIs execute simultaneously, rendering posters, synthesizing four domains of review content (Metacritic, IMDb, etc.), mapping Watchmode streaming metadata, and building a finalized, high-quality review screen.
5. **Step 5: LLM-as-Judge Evaluation:** The completely independent `Judge Agent` scans the generated content against the `UserProfile` dynamically and issues 5 distinct rubric validations ensuring accuracy, source coverage, and reasoning reliability.

## LLM-as-Judge

The internal verification step forces Gemini to behave as an auditor over its own multi-agent process, judging content on a 1-5 scale across:
- **Review Accuracy:** Evaluates aggregated metric mapping.
- **Recommendation Relevance:** Evaluates structural connections against user tastes.
- **Synthesis Quality:** Prevents generic output summaries.
- **Source Coverage:** Determines scrape efficacy.
- **Personalisation Depth:** Audits custom taste connection formatting.

## Deployment

**Streamlit Community Cloud (Recommended):**
Link your GitHub repo to Streamlit for near instant deployment at absolutely zero cost. Streamlit automatically detects the `requirements.txt` file and sets the build commands. Securely inject your Secrets in the Streamlit Dashboard.

**Railway for FastAPI:**
Should you extend Reelogue off the Streamlit frontend to operate strictly via the `api.py` endpoint, deploy simply to Railway using Docker or local environment mapping tools.

## Live Demo
- **Live app:** [your-app.streamlit.app]
- **Demo video:** [Loom link]

## Team
- **Role A (Architect & Integrator):** Project framework and API management.
- **Role B (Builder & Deployer):** Feature construction and delivery workflow. 

## License
MIT License
