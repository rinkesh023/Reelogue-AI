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

# --- PAGE CONFIG ---
st.set_page_config(page_title="Reelogue", page_icon="🎬", layout="wide")

# =====================================================================
# PREMIUM CSS DESIGN SYSTEM
# =====================================================================
st.markdown('<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">', unsafe_allow_html=True)
try:
    with open("static/style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

# =====================================================================
# INIT SESSION STATE (persistent across refreshes)
# =====================================================================
_params = st.query_params
if "sid" in _params:
    _session_id = _params["sid"]
else:
    _session_id = str(uuid.uuid4())
    st.query_params["sid"] = _session_id

if "session_id" not in st.session_state or st.session_state.session_id != _session_id:
    st.session_state.session_id = _session_id

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

# --- RELOAD PROFILE FROM DB ON FRESH PAGE LOAD ---
if st.session_state.profile_data is None:
    try:
        _r = requests.get(f"{API_URL}/profile/{st.session_state.session_id}")
        if _r.status_code == 200:
            st.session_state.profile_data = _r.json().get("profile")
    except Exception:
        pass

GENRES_LIST = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", 
               "Drama", "Family", "Fantasy", "History", "Horror", "Mystery", 
               "Romance", "Sci-Fi", "Thriller", "World Cinema", "Slow-burn"]

# =====================================================================
# API HELPERS
# =====================================================================
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


def render_radial_score(label, value, max_val=10, size=90):
    """Generate an SVG radial progress bar for scores."""
    try:
        num = float(str(value).replace('%','').strip())
    except (ValueError, TypeError):
        return f'<div class="score-radial"><span style="color:var(--text-muted);font-size:12px;">{label}</span><span style="color:var(--text-secondary);font-size:18px;font-weight:700;">{value}</span></div>'
    
    pct = min(num / max_val, 1.0) if max_val > 0 else 0
    r = 36
    circ = 2 * 3.14159 * r
    dash = circ * pct
    gap = circ - dash
    
    # Color based on percentage
    if pct >= 0.75:
        color = "#10B981"
    elif pct >= 0.5:
        color = "#F59E0B"
    else:
        color = "#EF4444"
    
    svg = f'''
    <div class="score-radial">
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
            <circle cx="{size//2}" cy="{size//2}" r="{r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="6"/>
            <circle cx="{size//2}" cy="{size//2}" r="{r}" fill="none" stroke="{color}" stroke-width="6"
                stroke-dasharray="{dash} {gap}" stroke-linecap="round"
                transform="rotate(-90 {size//2} {size//2})"
                style="transition: stroke-dasharray 1s ease-out;">
                <animate attributeName="stroke-dasharray" from="0 {circ}" to="{dash} {gap}" dur="1s" fill="freeze"/>
            </circle>
            <text x="{size//2}" y="{size//2 + 1}" text-anchor="middle" dominant-baseline="middle"
                fill="{color}" font-size="16" font-weight="700" font-family="Plus Jakarta Sans, sans-serif">{value}</text>
        </svg>
        <span style="color:var(--text-muted);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">{label}</span>
    </div>'''
    return svg


# =====================================================================
# SIDEBAR NAVIGATION
# =====================================================================
with st.sidebar:
    st.markdown('<div class="logo-text">Reelogue</div>', unsafe_allow_html=True)
    
    if st.session_state.profile_data:
        p_name = st.session_state.profile_data.get("name") or "User"
        char = p_name[0].upper()
    else:
        p_name = "New User"
        char = "U"
        
    st.markdown(f"""
    <div class="user-card">
        <div class="user-avatar">{char}</div>
        <div>
            <div class="user-info-name">{p_name}</div>
            <div class="user-info-status">● Active Session</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    nav = st.radio("MENU", ["Home", "Reelogue AI", "Watchlist", "My Reviews", "Settings"], label_visibility="hidden")

    # Clear global search if user clicks a different nav item
    if "last_nav" not in st.session_state:
        st.session_state.last_nav = nav
    if nav != st.session_state.last_nav:
        st.session_state.global_search_active = False
        st.session_state.last_nav = nav


# =====================================================================
# HELPER: RENDER FULL REVIEW (PREMIUM)
# =====================================================================
def render_full_review_ui(review, is_search=False):
    meta = review.get("metadata", {})
    synth = review.get("synthesis", {})
    title = meta.get('title', 'Unknown')
    year = meta.get('release_year', 'N/A')
    trailer = meta.get('trailer_key')
    
    st.markdown("---")
    
    # -- Hero Section --
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
        st.markdown(f"## {title}")
        st.caption(f"{year} • Directed by {meta.get('director', 'N/A')}")
        if meta.get('genres'):
            genre_html = " ".join([f'<span style="display:inline-block;background:rgba(139,92,246,0.12);border:1px solid rgba(139,92,246,0.3);color:#C4B5FD;padding:4px 12px;border-radius:50px;font-size:12px;font-weight:500;margin:2px;">{g}</span>' for g in meta.get('genres')])
            st.markdown(genre_html, unsafe_allow_html=True)
        
        st.write("")
        verdict_score = synth.get("reelogue_rating", "N/A")
        st.markdown(f'''
        <div style="background:linear-gradient(135deg, rgba(139,92,246,0.15), rgba(6,182,212,0.1)); border:1px solid rgba(139,92,246,0.25); border-radius:16px; padding:20px; margin:12px 0;">
            <div style="color:var(--text-muted);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;">Reelogue Verdict</div>
            <div style="font-size:32px;font-weight:800;background:linear-gradient(135deg,#8B5CF6,#06B6D4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:4px 0;">{verdict_score}/10</div>
            <div style="color:var(--text-secondary);font-size:14px;font-style:italic;">"{synth.get('verdict', 'N/A')}"</div>
        </div>
        ''', unsafe_allow_html=True)
        
    # -- Aggregated Scores — Radial Progress Bars --
    st.markdown("---")
    st.markdown('<div class="section-label">Aggregated Review Scores</div>', unsafe_allow_html=True)
    scores = synth.get("scores", {})
    
    score_items = [
        ("IMDb", scores.get("imdb", "N/A"), 10),
        ("RT Critics", scores.get("rotten_tomatoes_critics", "N/A"), 100),
        ("RT Audience", scores.get("rotten_tomatoes_audience", "N/A"), 100),
        ("Metacritic", scores.get("metacritic", "N/A"), 100),
        ("Letterboxd", scores.get("letterboxd", "N/A"), 5),
    ]
    
    cols = st.columns(5)
    for idx, (label, val, mx) in enumerate(score_items):
        with cols[idx]:
            display_val = f"{val}/{mx}" if str(val) != "N/A" and "%" not in str(val) else str(val)
            st.metric(label=label, value=display_val)
    
    st.markdown("---")
    
    # -- Summary, Critics, Audience --
    st.markdown('<div class="section-label">Summary</div>', unsafe_allow_html=True)
    st.write(synth.get('summary', 'N/A'))
    
    c_crit, c_aud = st.columns(2)
    with c_crit:
        st.markdown('<div class="section-label">Critic Consensus</div>', unsafe_allow_html=True)
        st.write(synth.get('critic_consensus', 'N/A'))
    with c_aud:
        st.markdown('<div class="section-label">Audience Take</div>', unsafe_allow_html=True)
        st.write(synth.get('audience_take', 'N/A'))
    
    st.markdown("---")
    
    # -- Streaming --
    st.markdown('<div class="section-label">Streaming Availability</div>', unsafe_allow_html=True)
    st.write(review.get('streaming_raw', 'N/A'))
    
    # -- Best For / Avoid If — Pill Badges --
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="section-label">Best For</div><div class="badge-best">✅ {synth.get("best_for", "N/A")}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="section-label">Avoid If</div><div class="badge-avoid">⚠️ {synth.get("avoid_if", "N/A")}</div>', unsafe_allow_html=True)

    # -- Trailer --
    if trailer:
        st.markdown("---")
        st.markdown('<div class="section-label">Trailer</div>', unsafe_allow_html=True)
        st.video(f"https://www.youtube.com/watch?v={trailer}")
    
    # -- Judge Evaluation --
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
            st.markdown(render_radial_score("Audit Score", f"{judge.get('overall_score', 0):.1f}", 5, 100), unsafe_allow_html=True)
            st.write(f"**Top Strength:** {judge.get('top_strength', 'N/A')}")
            for crit, label in [("review_accuracy", "Accuracy"), ("recommendation_relevance", "Relevance"), ("synthesis_quality", "Synthesis")]:
                st.progress(judge.get("scores", {}).get(crit, 0) / 5.0, text=f"{label}: {judge.get('reasoning', {}).get(crit, '')}")


# =====================================================================
# PAGE DEFINITIONS
# =====================================================================

if st.session_state.global_search_active and (st.session_state.active_review or st.session_state.chat_results):
    st.markdown(f'<div class="section-label">Search & Analysis</div>', unsafe_allow_html=True)
    st.title("Search & Analysis")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.global_search_active = False
        st.session_state.chat_results = None
        st.session_state.active_review = None
        st.rerun()
        
    if st.session_state.active_review:
        render_full_review_ui(st.session_state.active_review, is_search=True)
    elif st.session_state.chat_results:
        st.markdown(f"### Results for *'{st.session_state.search_query}'*")
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
                            elif r.status_code == 429:
                                st.error("Rate limit reached. Please wait a moment.")
                            else:
                                st.error(f"Error: Backend failed to generate review. Code {r.status_code}")
                    if st.button("➕ Watchlist", key=f"csqadd_{row_idx}_{i}", use_container_width=True):
                        add_to_watchlist(rec.get('title'), str(rec.get('year')), rec.get('type', 'Movie'), "Want to Watch", 0, "", poster)
                        st.toast("Added!")

elif nav == "Home":
    # -- Greeting Banner (animated mesh gradient) --
    if st.session_state.profile_data:
        name = st.session_state.profile_data.get("name", "User")
        tastes = ", ".join(st.session_state.profile_data.get("favourite_genres", [])[:3])
        hour = datetime.now().hour
        if hour < 12: greeting = "Good morning"
        elif hour < 17: greeting = "Good afternoon"
        else: greeting = "Good evening"
        
        st.markdown(f"""
        <div class="greeting-banner">
            <h2>{greeting}, {name} 👋</h2>
            <p>What are you watching tonight? Your taste — {tastes}.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="greeting-banner">
            <h2>Welcome to Reelogue 🎬</h2>
            <p>Your AI-powered cinema companion. Head to Settings to build your taste profile.</p>
        </div>
        """, unsafe_allow_html=True)
        
    if st.button("✨ Generate AI Picks", use_container_width=False):
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
        st.markdown('<div class="section-label">AI Picks For You</div>', unsafe_allow_html=True)
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

    st.markdown("---")

    # -- Recent Activity Panels --
    c1, c_space, c2 = st.columns([1, 0.1, 1])
    with c1:
        st.markdown('<div class="section-label">Recently Watched</div>', unsafe_allow_html=True)
        recent = get_watchlist("Watched")[:3]
        if not recent:
            st.caption("No watched films yet.")
        for r in recent:
            with st.container(border=True):
                st.write(f"**{r.get('title')}** ({r.get('year')})")
                if int(r.get('user_rating') or 0) > 0:
                    st.caption(f"{'⭐'*int(r.get('user_rating') or 0)} — {r.get('user_comment')}")
    with c2:
        st.markdown('<div class="section-label">Latest Additions</div>', unsafe_allow_html=True)
        reviews = get_watchlist()[:3]
        if not reviews:
            st.caption("No items in watchlist yet.")
        for r in reviews:
            with st.container(border=True):
                st.write(f"**{r.get('title')}** ({r.get('year')})")
                st.caption(f"Status: {r.get('status')}")

elif nav == "Reelogue AI":
    st.markdown("""
    <div class="greeting-banner">
        <h2>Reelogue AI 🤖</h2>
        <p>Ask me to find movies by director, actor, genre, or mood. Use the search bar below.</p>
    </div>
    """, unsafe_allow_html=True)

elif nav == "Watchlist":
    st.title("Watchlist")
    t1, t2 = st.tabs(["📌 Want to Watch", "✍️ Manual Add"])
    with t1:
        items = get_watchlist("Want to Watch")
        if not items:
            st.info("Your watchlist is empty. Add films from the Home page or via AI search!")
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
    
    st.markdown('<div class="section-label">Your Taste Profile</div>', unsafe_allow_html=True)
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
                    st.success("Profile saved! Head back to Home.")
                else:
                    st.error(f"Backend failed to save profile: {r.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("📱 Cross-Device Access"):
        st.write("Share this link to access your session from any device:")
        _app_base_url = os.getenv("STREAMLIT_URL", "https://your-app-name.streamlit.app")
        share_url = f"{_app_base_url}?sid={st.session_state.session_id}"
        st.code(share_url, language=None)
        st.caption("Anyone with this link can view and modify your watchlist & profile.")

    with st.expander("⚠️ Advanced Options (Reset & New Session)"):
        st.warning("These actions will affect your current session data permanently.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔴 Delete All Data", type="primary", use_container_width=True):
                try:
                    r = requests.delete(f"{API_URL}/reset/{st.session_state.session_id}")
                    if r.status_code == 200:
                        st.session_state.profile_data = None
                        st.session_state.recommendations = None
                        st.session_state.active_review = None
                        st.session_state.judge_eval = None
                        st.session_state.chat_results = None
                        st.success("All data has been reset!")
                        st.rerun()
                    else:
                        st.error(f"Reset failed: {r.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        with col2:
            if st.button("🆕 Start Fresh Session", use_container_width=True):
                new_sid = str(uuid.uuid4())
                st.session_state.session_id = new_sid
                st.session_state.profile_data = None
                st.session_state.recommendations = None
                st.session_state.active_review = None
                st.session_state.judge_eval = None
                st.session_state.chat_results = None
                st.query_params["sid"] = new_sid
                st.rerun()

# =====================================================================
# GLOBAL AI SEARCH BAR
# =====================================================================
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
