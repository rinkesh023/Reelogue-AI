import os
import streamlit as st
import importlib
from dotenv import load_dotenv
from datetime import datetime
import json
import requests
import uuid

# Load environment variables
load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

# --- CSS INJECTIONS FOR UI ---
st.set_page_config(page_title="Reelogue", page_icon="🎬", layout="wide")

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

# --- INIT SESSION STATE ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "profile_data" not in st.session_state:
    st.session_state.profile_data = None
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
if "chat_results" not in st.session_state:
    st.session_state.chat_results = None

GENRES_LIST = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", 
               "Drama", "Family", "Fantasy", "History", "Horror", "Mystery", 
               "Romance", "Sci-Fi", "Thriller", "World Cinema", "Slow-burn"]

# --- API HELPERS ---
def get_watchlist(status_filter=None):
    try:
        url = f"{API_URL}/watchlist/{st.session_state.session_id}"
        if status_filter:
            url += f"?status={status_filter}"
        r = requests.get(url)
        if r.status_code == 200:
            return r.json().get("watchlist", [])
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
    return []

def add_to_watchlist(title, year, m_type, status, user_rating, user_comment, poster_url=""):
    try:
        requests.post(f"{API_URL}/watchlist", json={
            "session_id": st.session_state.session_id,
            "title": title,
            "year": year,
            "m_type": m_type,
            "status": status,
            "user_rating": user_rating,
            "user_comment": user_comment,
            "poster_url": poster_url
        })
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("""
    <div style="font-family: Georgia, serif; font-size: 32px; font-style: italic; color: #ff7f50; padding-bottom: 24px;">
        Reelogue
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.profile_data:
        p_name = st.session_state.profile_data.get("name") or "User"
        char = p_name[0].upper()
    else:
        p_name = "New User"
        char = "U"
        
    st.markdown(f"""
    <div style="background-color: var(--secondary-background-color); border: 1px solid var(--border-color); padding: 12px; border-radius: 12px; display: flex; align-items: center; margin-bottom: 30px;">
        <div style="background-color: #3f2623; color: #ffa384; border-radius: 50%; width: 44px; height: 44px; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 20px; margin-right: 14px;">
            {char}
        </div>
        <div>
            <div style="color: var(--text-color); font-weight: 600; font-size: 16px;">{p_name}</div>
            <div style="color: #ffc266; font-size: 13px;">Active Session</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
            if st.button("Run AI Safety Checks"):
                with st.spinner("Running AI safety checks..."):
                    try:
                        r = requests.post(f"{API_URL}/judge", json={
                            "session_id": st.session_state.session_id,
                            "review_data": review
                        })
                        if r.status_code == 200:
                            st.session_state.judge_eval = r.json()
                            st.rerun()
                        elif r.status_code == 429:
                            st.error("Wait 60s for Judge (Rate Limit)")
                        else:
                            st.error(f"Error: {r.text}")
                    except Exception as e:
                        st.error(f"Error auditing review: {e}")
                        
        judge = st.session_state.judge_eval
        if judge:
            st.metric("Internal Audit Score", f"{judge.get('overall_score', 0):.1f} / 5")
            st.write(f"**Top Strength:** {judge.get('top_strength', 'N/A')}")
            for crit, label in [("review_accuracy", "Accuracy Check"), ("recommendation_relevance", "Relevance Check"), ("synthesis_quality", "Synthesis Integrity")]:
                st.progress(judge.get("scores", {}).get(crit, 0) / 5.0, text=f"{label}: {judge.get('reasoning', {}).get(crit, '')}")

# ----------------------------------------------------
# PAGE DEFINITIONS
# ----------------------------------------------------

if st.session_state.global_search_active and (st.session_state.active_review or st.session_state.chat_results):
    st.title("Search & Analysis")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.global_search_active = False
        st.session_state.chat_results = None
        st.session_state.active_review = None
        st.rerun()
        
    if st.session_state.active_review:
        render_full_review_ui(st.session_state.active_review, is_search=True)
    elif st.session_state.chat_results:
        st.write(f"### Found these results for '{st.session_state.search_query}':")
        chunk_size = 5
        for row_idx in range(0, len(st.session_state.chat_results), chunk_size):
            chunk = st.session_state.chat_results[row_idx:row_idx + chunk_size]
            cols = st.columns(chunk_size)
            for i, rec in enumerate(chunk):
                with cols[i]:
                    poster = rec.get("poster_url", "")
                    if poster: st.image(poster, use_container_width=True)
                    st.markdown(f"**{rec.get('title')}**")
                    st.caption(f"{rec.get('year')} • {rec.get('type')}")
                    st.info(rec.get('why_you_will_love_it', 'Great match!'))
                    
                    if st.button("Review", key=f"cs_{row_idx}_{i}", use_container_width=True):
                        with st.spinner(f"Reviewing {rec.get('title')}..."):
                            r = requests.post(f"{API_URL}/review", json={
                                "session_id": st.session_state.session_id,
                                "title": str(rec.get('title')), "year": str(rec.get('year'))
                            })
                            if r.status_code == 200:
                                st.session_state.active_review = r.json()
                                st.session_state.judge_eval = None
                                st.rerun()
                    if st.button("➕ Watchlist", key=f"csqadd_{row_idx}_{i}", use_container_width=True):
                        add_to_watchlist(rec.get('title'), str(rec.get('year')), rec.get('type', 'Movie'), "Want to Watch", 0, "", poster)
                        st.toast("Added!")

elif nav == "Home":
    st.title("Home")
    
    if st.session_state.profile_data:
        name = st.session_state.profile_data.get("name", "User")
        tastes = ", ".join(st.session_state.profile_data.get("favourite_genres", [])[:3])
        st.subheader(f"Good evening, {name}. What are you watching tonight?")
        st.markdown(f"<span style='color:#a3a3a3;'>Based on your taste — {tastes}. Updated just now.</span>", unsafe_allow_html=True)
        st.write("")
    else:
        st.subheader("Welcome to Reelogue.")
        st.write("Please configure your profile in Settings to get started.")
        
    if st.button("Generate AI Picks"):
        if st.session_state.profile_data:
            with st.spinner("Generating highly personalized recommendations..."):
                try:
                    r = requests.post(f"{API_URL}/recommendations", json={"session_id": st.session_state.session_id})
                    if r.status_code == 200:
                        st.session_state.recommendations = r.json().get("recommendations", [])
                        st.session_state.active_review = None 
                    elif r.status_code == 429:
                        st.error(r.json().get("detail", "Rate limit reached."))
                    else:
                        st.error(f"Backend Error: {r.text}")
                except Exception as e:
                    st.error(f"Error fetching recommendations: {e}")
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
                            try:
                                r = requests.post(f"{API_URL}/review", json={
                                    "session_id": st.session_state.session_id,
                                    "title": str(rec.get('title')),
                                    "year": str(rec.get('year'))
                                })
                                if r.status_code == 200:
                                    st.session_state.active_review = r.json()
                                    st.session_state.judge_eval = None
                                elif r.status_code == 429:
                                    st.error(r.json().get("detail", "Rate limit reached."))
                                else:
                                    st.error("Error from backend.")
                            except Exception as e:
                                st.error(f"Error connecting to backend: {e}")
                    
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
                st.write(f"**{r.get('title')}** ({r.get('year')}) - {r.get('status')}")
                if int(r.get('user_rating') or 0) > 0:
                    st.caption(f"{'⭐'*int(r.get('user_rating') or 0)} - {r.get('user_comment')}")
    with c2:
        st.markdown("### Latest Additions")
        reviews = get_watchlist()[:3]
        for r in reviews:
            with st.container(border=True):
                st.write(f"**{r.get('title')}** ({r.get('year')})")
                st.caption(f"Status: {r.get('status')}")

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
                    if r.get('poster_url'): 
                        st.image(r.get('poster_url'), width=80)
                with colB:
                    st.markdown(f"#### {r.get('title')} ({r.get('year')})")
                    st.caption(f"Added: {r.get('added_at')}")
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
                if r.get('poster_url'): st.image(r.get('poster_url'), width=80)
            with colB:
                st.markdown(f"#### {r.get('title')} ({r.get('year')})")
                st.write(f"Rating: {'⭐'*int(r.get('user_rating') or 0)}")
                if r.get('user_comment'):
                    st.write(f"> {r.get('user_comment')}")

elif nav == "Settings":
    st.title("Settings")
    
    st.header("Your Taste Profile")
    with st.form("onboarding_form"):
        p_data = st.session_state.profile_data or {}
        name = st.text_input("Your Name", value=p_data.get("name", ""))
        fav_genres = st.multiselect("Favourite Genres", GENRES_LIST, default=p_data.get("favourite_genres", []))
        fav_films = st.text_input("Favourite Films/Series (comma-separated)", value=",".join(p_data.get("favourite_films", [])))
        mood = st.selectbox("Current Mood", ["Want something light", "Need to cry", "Mind-bending", "Edge of my seat", "Inspiring"])
        viewing_context = st.selectbox("Viewing Context", ["Solo", "Date Night", "Family", "With Friends"])
        content_type = st.radio("Content Type", ["movies", "series", "both"], horizontal=True)
        streaming = st.multiselect("Streaming Services", ["Netflix", "Amazon Prime", "Hulu", "Disney+", "Max", "Apple TV+"], default=p_data.get("streaming_services", []))
        language_preference = st.multiselect("Regional Cinema Preference", ["Hollywood", "Bollywood", "South Indian Movies", "Global / World Cinema"], default=p_data.get("language_preference", []))

        if st.form_submit_button("Save Profile"):
            new_profile = {
                "session_id": st.session_state.session_id,
                "name": name,
                "favourite_genres": fav_genres,
                "favourite_films": [f.strip() for f in fav_films.split(",") if f.strip()],
                "mood": mood,
                "viewing_context": viewing_context,
                "content_type": content_type,
                "streaming_services": streaming,
                "language_preference": language_preference
            }
            try:
                r = requests.post(f"{API_URL}/profile", json=new_profile)
                if r.status_code == 200:
                    st.session_state.profile_data = new_profile
                    st.success("Profile saved dynamically to Backend! Head back to Home.")
                else:
                    st.error(f"Backend failed to save profile: {r.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")

# ----------------------------------------------------
# GLOBAL AGENT SEARCH BAR (Appears Universal)
# ----------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
search_query = st.chat_input("Ask Reelogue AI for movies by director, actor, genre, or mood...")

if search_query:
    st.session_state.search_query = search_query
    
if st.session_state.search_query and search_query:
    with st.spinner(f"Finding best matches for '{st.session_state.search_query}'..."):
        try:
            r = requests.post(f"{API_URL}/chat_search", json={
                "session_id": st.session_state.session_id,
                "query": st.session_state.search_query
            })
            if r.status_code == 200:
                st.session_state.chat_results = r.json().get("results", [])
                st.session_state.active_review = None
                st.session_state.judge_eval = None
                st.session_state.global_search_active = True
                st.rerun()
            elif r.status_code == 429:
                st.warning(r.json().get("detail", "Rate limit reached."))
                st.session_state.search_query = ""
            else:
                st.error(f"Server error: {r.text}")
        except Exception as e:
            st.error(f"Error analyzing film: {e}")
