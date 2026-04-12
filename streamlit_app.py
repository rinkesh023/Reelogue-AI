import os
import sqlite3
import streamlit as st
import importlib
from dotenv import load_dotenv
from datetime import datetime
import json
import google.generativeai as genai

# Load environment variables
load_dotenv()

from memory.user_profile import UserProfile
from agents import recommendation_agent, review_agent, judge_agent

# --- CSS INJECTIONS FOR UI ---
st.set_page_config(page_title="Reelogue", page_icon="🎬", layout="wide")

st.markdown("""
<style>
/* Mimicking the dark sophisticated UI */
[data-testid="stSidebar"] {
    background-color: #121212;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* Push settings to the bottom exclusively in the sidebar */
[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(5) {
    margin-top: 35vh;
    border-top: 1px solid #333;
    border-radius: 0;
}
</style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
DB_NAME = "reelogue.db"
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist
                 (id INTEGER PRIMARY KEY, title TEXT, year TEXT, type TEXT, status TEXT, user_rating INTEGER, user_comment TEXT, poster_url TEXT, date_added TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_watchlist(status_filter=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if status_filter:
        c.execute('SELECT * FROM watchlist WHERE status=? ORDER BY id DESC', (status_filter,))
    else:
        c.execute('SELECT * FROM watchlist ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return rows

def add_to_watchlist(title, year, m_type, status, user_rating, user_comment, poster_url=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO watchlist (title, year, type, status, user_rating, user_comment, poster_url, date_added) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
              (title, year, m_type, status, user_rating, user_comment, poster_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# --- INIT SESSION STATE ---
if "profile" not in st.session_state:
    st.session_state.profile = None
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None
if "active_review" not in st.session_state:
    st.session_state.active_review = None
if "judge_eval" not in st.session_state:
    st.session_state.judge_eval = None
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "global_search_active" not in st.session_state:
    st.session_state.global_search_active = False

GENRES_LIST = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", 
               "Drama", "Family", "Fantasy", "History", "Horror", "Mystery", 
               "Romance", "Sci-Fi", "Thriller", "World Cinema", "Slow-burn"]

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("""
    <div style="font-family: Georgia, serif; font-size: 32px; font-style: italic; color: #ff7f50; padding-bottom: 24px;">
        Reelogue
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.profile:
        p_name = st.session_state.profile.name or "User"
        char = p_name[0].upper()
    else:
        p_name = "New User"
        char = "U"
        
    st.markdown(f"""
    <div style="background-color: #1A1A1A; border: 1px solid #333; padding: 12px; border-radius: 12px; display: flex; align-items: center; margin-bottom: 30px;">
        <div style="background-color: #3f2623; color: #ffa384; border-radius: 50%; width: 44px; height: 44px; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 20px; margin-right: 14px;">
            {char}
        </div>
        <div>
            <div style="color: white; font-weight: 600; font-size: 16px;">{p_name}</div>
            <div style="color: #ffc266; font-size: 13px;">Active Session</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Updated text to matching Reelogue AI. The exact 5th item is offset via CSS to the bottom corner
    nav = st.radio("MENU", ["Home", "Reelogue AI", "Watchlist", "My Reviews", "Settings"], label_visibility="hidden")

# --- HELPER: RENDER FULL REVIEW ---
def render_full_review_ui(review, is_search=False):
    meta = review.get("metadata", {})
    synth = review.get("synthesis", {})
    title = meta.get('title', 'Unknown')
    year = meta.get('release_year', 'N/A')
    trailer = meta.get('trailer_key')
    
    st.divider()
    st.header(f"{title} ({year})")
    
    colA, colB = st.columns([1, 2])
    with colA:
        poster = meta.get("poster_url")
        if poster:
            st.image(poster, use_container_width=True)
        with st.expander("➕ Add to Watchlist"):
            w_status = st.selectbox("Status", ["Want to Watch", "Watched"], key=f"ws_{title}_{is_search}")
            w_rating = st.slider("Rating (if watched)", 0, 5, 0, key=f"wr_{title}_{is_search}")
            w_comment = st.text_area("Review/Notes", key=f"wc_{title}_{is_search}")
            if st.button("Save", key=f"wb_{title}_{is_search}"):
                add_to_watchlist(title, year, "Movie/Series", w_status, w_rating, w_comment, poster)
                st.success("Saved!")
                
    with colB:
        st.write(f"**Director:** {meta.get('director', 'N/A')}")
        if meta.get('genres'):
            st.write(f"**Genres:** {', '.join(meta.get('genres'))}")
        st.metric("Reelogue Verdict Score", synth.get("reelogue_rating", "N/A"))
        st.info(f"**Verdict:** {synth.get('verdict', 'N/A')}")
        
    st.markdown("---")
    st.subheader("Aggregated Review Scores")
    score_cols = st.columns(5)
    scores = synth.get("scores", {})
    with score_cols[0]: st.metric("IMDb", scores.get("imdb", "N/A"))
    with score_cols[1]: st.metric("RT Critics", scores.get("rotten_tomatoes_critics", "N/A"))
    with score_cols[2]: st.metric("RT Audience", scores.get("rotten_tomatoes_audience", "N/A"))
    with score_cols[3]: st.metric("Metacritic", scores.get("metacritic", "N/A"))
    with score_cols[4]: st.metric("Letterboxd", scores.get("letterboxd", "N/A"))
    st.markdown("---")
    
    st.subheader("Summary")
    st.write(synth.get('summary', 'N/A'))
    
    st.subheader("Critic Consensus")
    st.write(synth.get('critic_consensus', 'N/A'))
    
    st.subheader("Audience Take")
    st.write(synth.get('audience_take', 'N/A'))
    
    st.subheader("Streaming Availability")
    st.write(review.get('streaming_raw', 'N/A'))
    
    c1, c2 = st.columns(2)
    with c1:
        st.success(f"**Best For:**\n\n{synth.get('best_for', 'N/A')}")
    with c2:
        st.error(f"**Avoid If:**\n\n{synth.get('avoid_if', 'N/A')}")

    if trailer:
        st.subheader("Trailer")
        st.video(f"https://www.youtube.com/watch?v={trailer}")
    
    with st.expander("🛡️ AI Reliability Audit (Verification)"):
        if st.session_state.judge_eval is None:
            with st.spinner("Running AI safety checks..."):
                st.session_state.judge_eval = judge_agent.evaluate_review(review, st.session_state.profile or UserProfile())
        judge = st.session_state.judge_eval
        if judge:
            st.metric("Internal Audit Score", f"{judge.get('overall_score', 0):.1f} / 5")
            st.write(f"**Top Strength:** {judge.get('top_strength', 'N/A')}")
            for crit, label in [("review_accuracy", "Accuracy Check"), ("recommendation_relevance", "Relevance Check"), ("synthesis_quality", "Synthesis Integrity")]:
                st.progress(judge.get("scores", {}).get(crit, 0) / 5.0, text=f"{label}: {judge.get('reasoning', {}).get(crit, '')}")

# ----------------------------------------------------
# PAGE DEFINITIONS
# ----------------------------------------------------

# If user submitted a global search via the chatbot, intercept traditional rendering!
if st.session_state.global_search_active and st.session_state.active_review:
    st.title("Search Analysis")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.global_search_active = False
        st.rerun()
    render_full_review_ui(st.session_state.active_review, is_search=True)

# Normal Page Rendering
elif nav == "Home":
    st.title("Home")
    
    if st.session_state.profile:
        name = st.session_state.profile.name or "User"
        tastes = ", ".join(st.session_state.profile.favourite_genres[:3])
        st.subheader(f"Good evening, {name}. What are you watching tonight?")
        st.markdown(f"<span style='color:#a3a3a3;'>Based on your taste — {tastes}. Updated just now.</span>", unsafe_allow_html=True)
        st.write("")
    else:
        st.subheader("Welcome to Reelogue.")
        st.write("Please configure your profile in Settings to get started.")
        
    if st.button("Generate AI Picks"):
        if st.session_state.profile:
            with st.spinner("Generating highly personalized recommendations..."):
                recs = recommendation_agent.get_recommendations(st.session_state.profile)
                st.session_state.recommendations = recs
                st.session_state.active_review = None 
        else:
            st.error("Please set a profile in Settings first!")

    if st.session_state.recommendations:
        st.markdown("### AI picks for you")
        # Split into chunks of 5 for multiple rows
        chunk_size = 5
        for row_idx in range(0, len(st.session_state.recommendations), chunk_size):
            chunk = st.session_state.recommendations[row_idx:row_idx + chunk_size]
            cols = st.columns(chunk_size)
            for i, rec in enumerate(chunk):
                with cols[i]:
                    poster = rec.get("poster_url", "")
                    if poster:
                        st.image(poster, use_container_width=True)
                    st.markdown(f"**{rec.get('title')}**")
                    st.caption(f"{rec.get('year')} • {rec.get('type')}")
                    match_score = rec.get('taste_match', 0)
                    st.progress(match_score / 100, text=f"{match_score}% Match")
                    
                    if st.button("Review", key=f"pick_{row_idx}_{i}", use_container_width=True):
                        with st.spinner(f"Reviewing {rec.get('title')} across all platforms..."):
                            review = review_agent.review_movie(str(rec.get('title')), str(rec.get('year')), st.session_state.profile)
                            st.session_state.active_review = review
                            st.session_state.judge_eval = None
                    
                    if st.button("➕ Watchlist", key=f"qadd_{row_idx}_{i}", use_container_width=True):
                        add_to_watchlist(rec.get('title'), str(rec.get('year')), rec.get('type', 'Movie'), "Want to Watch", 0, "", poster)
                        st.toast(f"{rec.get('title')} added to Watchlist!")
            st.markdown("<br>", unsafe_allow_html=True)
                    
    if st.session_state.active_review and not st.session_state.global_search_active:
        render_full_review_ui(st.session_state.active_review, is_search=False)

    st.divider()

    c1, c_space, c2 = st.columns([1, 0.1, 1])
    with c1:
        st.markdown("### Recently watched")
        recent = get_watchlist("Watched")[:3]
        for r in recent:
            with st.container(border=True):
                st.write(f"**{r[1]}** ({r[2]}) - {r[4]}")
                if int(r[5] or 0) > 0:
                    st.caption(f"{'⭐'*int(r[5] or 0)} - {r[6]}")
    with c2:
        st.markdown("### Latest Additions")
        reviews = get_watchlist()[:3]
        for r in reviews:
            with st.container(border=True):
                st.write(f"**{r[1]}** ({r[2]})")
                st.caption(f"Status: {r[4]}")

elif nav == "Reelogue AI":
    st.title("Reelogue AI")
    st.write("Instant Universal Search: Ask Reelogue AI to find and review any film and series.")

elif nav == "Watchlist":
    st.title("Watchlist")
    t1, t2 = st.tabs(["Want to Watch", "Manual Add File"])
    with t1:
        items = get_watchlist("Want to Watch")
        for r in items:
            with st.container(border=True):
                colA, colB = st.columns([1, 6])
                with colA:
                    if r[7]: 
                        st.image(r[7], width=80)
                with colB:
                    st.markdown(f"#### {r[1]} ({r[2]})")
                    st.caption(f"Added: {r[8]}")
    with t2:
        with st.form("manual"):
            m_title = st.text_input("Title")
            m_year = st.text_input("Year")
            m_type = st.selectbox("Type", ["Movie", "Series"])
            m_status = st.selectbox("Status", ["Want to Watch", "Watched"])
            m_rating = st.slider("Rating", 0, 5, 0)
            m_comment = st.text_area("Your Review")
            if st.form_submit_button("Add to Database"):
                if m_title:
                    add_to_watchlist(m_title, m_year, m_type, m_status, m_rating, m_comment, "")
                    st.success("Successfully logged!")
                    st.rerun()

elif nav == "My Reviews":
    st.title("My Reviews & Watched History")
    items = get_watchlist("Watched")
    if not items:
        st.info("You haven't logged any watched films yet.")
    for r in items:
        with st.container(border=True):
            colA, colB = st.columns([1, 6])
            with colA:
                if r[7]: st.image(r[7], width=80)
            with colB:
                st.markdown(f"#### {r[1]} ({r[2]})")
                st.write(f"Rating: {'⭐'*int(r[5] or 0)}")
                if r[6]:
                    st.write(f"> {r[6]}")

elif nav == "Settings":
    st.title("Settings")
    
    st.header("Your Taste Profile")
    with st.form("onboarding_form"):
        prof = st.session_state.profile
        name = st.text_input("Your Name", value=prof.name if prof else "")
        fav_genres = st.multiselect("Favourite Genres", GENRES_LIST, default=prof.favourite_genres if prof else [])
        fav_films = st.text_input("Favourite Films/Series (comma-separated)", value=",".join(prof.favourite_films) if prof else "")
        mood = st.selectbox("Current Mood", ["Want something light", "Need to cry", "Mind-bending", "Edge of my seat", "Inspiring"])
        viewing_context = st.selectbox("Viewing Context", ["Solo", "Date Night", "Family", "With Friends"])
        content_type = st.radio("Content Type", ["movies", "series", "both"], horizontal=True)
        streaming = st.multiselect("Streaming Services", ["Netflix", "Amazon Prime", "Hulu", "Disney+", "Max", "Apple TV+"], default=prof.streaming_services if prof else [])
        language_preference = st.multiselect("Regional Cinema Preference", ["Hollywood", "Bollywood", "South Indian Movies", "Global / World Cinema"], default=prof.language_preference if prof and getattr(prof, "language_preference", None) else [])

        if st.form_submit_button("Save Profile"):
            profile = UserProfile(
                name=name,
                favourite_genres=fav_genres,
                favourite_films=[f.strip() for f in fav_films.split(",") if f.strip()],
                mood=mood,
                viewing_context=viewing_context,
                content_type=content_type,
                streaming_services=streaming,
                language_preference=language_preference
            )
            st.session_state.profile = profile
            st.success("Profile saved globally! Head back to Home.")

# ----------------------------------------------------
# GLOBAL AGENT SEARCH BAR (Appears Universal)
# ----------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
search_query = st.chat_input("Ask Reelogue AI to find and analyze ANY film and series...")

if search_query:
    st.session_state.search_query = search_query
    
if st.session_state.search_query and search_query:
    with st.spinner(f"Scraping the web and evaluating '{st.session_state.search_query}'..."):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")
        extraction_prompt = f"Extract the movie title and the year from this query: '{st.session_state.search_query}'. Return strictly JSON like {{\"title\": \"Movie Title\", \"year\": \"YYYY\"}}. If year is unknown, put an empty string."
        resp = model.generate_content(extraction_prompt).text
        try:
            import re
            json_match = re.search(r'\{.*\}', resp, re.DOTALL)
            ext = json.loads(json_match.group(0))
            t_title = ext.get('title', st.session_state.search_query)
            t_year = ext.get('year', "")
        except:
            t_title = st.session_state.search_query
            t_year = ""
            
        st.session_state.active_review = review_agent.review_movie(t_title, t_year, st.session_state.profile or UserProfile())
        st.session_state.judge_eval = None
        st.session_state.search_query = ""
        st.session_state.global_search_active = True
        st.rerun()
