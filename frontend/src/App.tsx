/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { 
  Play, Plus, Star, TrendingUp, BarChart3, Quote, Tv, Ticket, Edit3, 
  HelpCircle, LogOut, Film, Compass, List, MessageSquare, Settings,
  User, Sparkles, Brain, Search, Loader2, Check
} from "lucide-react";
import { cn } from "@/src/lib/utils";

const SESSION_ID = "default-session";

// Reusable Metric Card
const MetricCard = ({ label, score, total, icon: Icon, colorClass }: any) => (
  <motion.div 
    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
    className="bg-surface-container-high/80 backdrop-blur-xl p-4 md:p-6 rounded-2xl flex items-center justify-between group hover:bg-surface-container-highest transition-colors border border-white/5"
  >
    <div className="space-y-1">
      <p className="text-on-surface-variant text-[10px] md:text-xs font-medium uppercase tracking-widest">{label}</p>
      <h3 className={cn("text-xl md:text-3xl font-serif italic", colorClass)}>
        {score}
        {total && <span className="text-xs md:text-sm text-on-surface-variant not-italic ml-1">/{total}</span>}
      </h3>
    </div>
    <div className={cn("w-10 h-10 md:w-12 md:h-12 rounded-xl flex items-center justify-center bg-opacity-10", colorClass.replace('text-', 'bg-').replace('400', '500').replace('500', '600'))}>
      <Icon size={20} />
    </div>
  </motion.div>
);

export default function App() {
  const [activeTab, setActiveTab] = useState("Home");
  const [globalName, setGlobalName] = useState("Cinephile");

  // Create session on load
  useEffect(() => {
    fetch("/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: SESSION_ID,
        name: "User",
        favourite_genres: ["Sci-Fi", "Thriller"],
        content_type: "both"
      })
    }).catch(e => console.error("Could not register session", e));
  }, []);

  const navItems = [
    { icon: Film, label: "Home" },
    { icon: Compass, label: "Discover AI" },
    { icon: List, label: "Watchlist" },
    { icon: MessageSquare, label: "My Reviews" },
    { icon: Settings, label: "Settings" },
  ];

  return (
    <div className="min-h-screen bg-background text-on-surface selection:bg-primary selection:text-on-primary font-sans">
      {/* Sidebar Navigation */}
      <nav className="h-screen w-64 fixed left-0 top-0 bg-zinc-950 flex flex-col p-6 space-y-4 z-50 hidden md:flex border-r border-white/5">
        <div className="text-2xl font-serif italic text-primary mb-8">Reelogue</div>
        
        <div className="flex items-center space-x-3 mb-8 p-3 rounded-xl bg-surface-container-low border border-white/5">
          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
            {globalName.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="text-sm font-bold">{globalName}</p>
            <p className="text-xs text-tertiary">Active Session</p>
          </div>
        </div>

        <div className="space-y-2 flex-grow">
          {navItems.map((item) => (
            <button
              key={item.label}
              onClick={() => setActiveTab(item.label)}
              className={cn(
                "w-full flex items-center space-x-3 p-3 rounded-lg transition-all group",
                activeTab === item.label
                  ? "text-tertiary font-bold bg-white/5" 
                  : "text-zinc-500 hover:text-zinc-200 hover:bg-white/5"
              )}
            >
              <item.icon size={20} />
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </div>
      </nav>
      
      <main className="md:ml-64 min-h-screen flex flex-col">
        {activeTab === "Home" && <HomeTab setActiveTab={setActiveTab} globalName={globalName} setGlobalName={setGlobalName} />}
        {activeTab === "Discover AI" && <DiscoverTab />}
        {activeTab === "Watchlist" && <WatchlistTab />}
        {activeTab === "My Reviews" && <MyReviewsTab />}
        {activeTab === "Settings" && (
          <div className="p-12 h-screen flex items-center justify-center text-zinc-500">
            Settings Panel Coming Soon...
          </div>
        )}
      </main>
    </div>
  );
}

function HomeTab({ setActiveTab, globalName, setGlobalName }: { setActiveTab: (t: string) => void, globalName: string, setGlobalName: (n: string) => void }) {
  const [profile, setProfile] = useState({ name: globalName, genres: "Sci-Fi, Cyberpunk", mood: "Mind-bending", contentType: "both" });
  const [isSaving, setIsSaving] = useState(false);
  const [recommendations, setRecommendations] = useState<any[]>([]);

  const saveProfile = async () => {
    setIsSaving(true);
    await fetch("/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: SESSION_ID,
        name: profile.name,
        mood: profile.mood,
        content_type: profile.contentType,
        favourite_genres: profile.genres.split(",").map(g => g.trim()),
      })
    });
    setGlobalName(profile.name || "Anonymous");
    
    const res = await fetch("/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: SESSION_ID })
    });
    const d = await res.json();
    setRecommendations(d.recommendations || []);
    setIsSaving(false);
  };

  const addRecToWatchlist = async (rec: any) => {
    await fetch("/watchlist", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: SESSION_ID,
        title: rec.title,
        year: rec.year,
        poster_url: rec.poster_url || ""
      })
    });
    alert(`${rec.title} added to Watchlist!`);
  };

  return (
    <div className="p-12 max-w-7xl mx-auto w-full pt-16 h-screen overflow-y-auto">
      <h1 className="text-5xl font-serif italic mb-4">Welcome to Reelogue.</h1>
      <p className="text-xl text-zinc-400 mb-12">The AI companion that knows your taste better than you do.</p>
      
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-4 bg-surface-container-low p-8 rounded-3xl border border-white/5 space-y-6 h-fit">
          <h2 className="text-2xl font-serif text-tertiary">Tune your AI Agent</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-zinc-500 mb-2">What is your Name?</label>
              <input type="text" value={profile.name} onChange={e => setProfile({...profile, name: e.target.value})} className="w-full bg-zinc-900 border border-white/10 rounded-xl p-3 text-white focus:border-primary outline-none" />
            </div>
            <div>
              <label className="block text-sm text-zinc-500 mb-2">Favorite Genres (comma separated)</label>
              <input type="text" value={profile.genres} onChange={e => setProfile({...profile, genres: e.target.value})} className="w-full bg-zinc-900 border border-white/10 rounded-xl p-3 text-white focus:border-primary outline-none" />
            </div>
            <div>
              <label className="block text-sm text-zinc-500 mb-2">Current Mood</label>
              <input type="text" value={profile.mood} onChange={e => setProfile({...profile, mood: e.target.value})} className="w-full bg-zinc-900 border border-white/10 rounded-xl p-3 text-white focus:border-primary outline-none" />
            </div>
            <div>
              <label className="block text-sm text-zinc-500 mb-2">What do you want to watch?</label>
              <select value={profile.contentType} onChange={e => setProfile({...profile, contentType: e.target.value})} className="w-full bg-zinc-900 border border-white/10 rounded-xl p-3 text-white focus:border-primary outline-none">
                <option value="both">Mix of Both</option>
                <option value="Movies">Movies Only</option>
                <option value="Series">TV Series Only</option>
              </select>
            </div>

            <div className="pt-4 flex gap-4">
              <button 
                onClick={saveProfile} 
                disabled={isSaving}
                className="bg-primary text-black font-bold py-3 px-6 rounded-xl hover:scale-105 transition-transform flex gap-2 flex-grow justify-center disabled:opacity-50"
              >
                {isSaving ? <Loader2 className="animate-spin" size={20}/> : <><Sparkles size={20}/> Get Suggestions</>}
              </button>
            </div>
          </div>
        </div>

        <div className="lg:col-span-8">
          <h2 className="text-2xl font-serif italic mb-6">AI Hand-Picked For You</h2>
          {recommendations.length === 0 ? (
            <div className="h-64 border border-dashed border-white/10 rounded-3xl flex flex-col items-center justify-center text-zinc-600">
              <Brain size={48} className="mb-4 opacity-50" />
              <p>Update your taste profile on the left to generate matches.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {recommendations.map((rec, i) => (
                <div key={i} className="bg-surface-container-high rounded-2xl overflow-hidden border border-white/5 flex flex-col h-full group hover:border-primary/30 transition-colors">
                  <div className="h-48 w-full relative overflow-hidden bg-black/50">
                    <img src={rec.poster_url} className="w-full h-full object-cover opacity-60 group-hover:opacity-90 transition-opacity" />
                    <div className="absolute bottom-2 left-4">
                      <h3 className="font-bold text-white text-xl drop-shadow-md">{rec.title}</h3>
                      <p className="text-xs text-zinc-300 drop-shadow-md">{rec.year} • Match: {rec.taste_match}%</p>
                    </div>
                  </div>
                  <div className="p-5 flex-grow flex flex-col justify-between space-y-4">
                    <p className="text-sm text-zinc-400 italic line-clamp-3">"{rec.reason}"</p>
                    <button 
                      onClick={() => addRecToWatchlist(rec)}
                      className="w-full py-2 bg-white/5 hover:bg-primary/20 hover:text-primary rounded-lg text-sm font-bold transition-colors flex items-center justify-center gap-2"
                    >
                      <Plus size={16} /> Add to Watchlist
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// DISCOVER / SEARCH TAB
// -------------------------------------------------------------
function DiscoverTab() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [reviewData, setReviewData] = useState<any>(null);
  const [error, setError] = useState("");
  const [addedWatchlist, setAddedWatchlist] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsLoading(true); setError(""); setReviewData(null); setAddedWatchlist(false);

    try {
      const res = await fetch("/review", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: SESSION_ID, title: searchQuery, year: "" })
      });
      if (!res.ok) throw new Error("Agent failed. Check terminal.");
      setReviewData(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddWatchlist = async () => {
    if (!reviewData) return;
    await fetch("/watchlist", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: SESSION_ID,
        title: reviewData.metadata.title,
        year: reviewData.metadata.release_year,
        poster_url: reviewData.metadata.poster_url || ""
      })
    });
    setAddedWatchlist(true);
  };

  return (
    <>
      <div className="w-full bg-zinc-950 p-6 border-b border-white/5 sticky top-0 z-40">
          <form onSubmit={handleSearch} className="max-w-4xl mx-auto flex gap-4">
            <div className="relative flex-grow">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-500">
                <Search size={20} />
              </div>
              <input
                type="text" placeholder="Ask the AI agent to review any movie..."
                value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-surface-container-low border border-white/10 rounded-full py-4 pl-12 pr-6 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 text-white transition-all shadow-inner"
              />
            </div>
            <button type="submit" disabled={isLoading} className="px-8 py-4 rounded-full bg-gradient-to-r from-primary to-primary-container text-on-primary font-bold flex items-center space-x-2 neon-glow hover:scale-[1.02] transition-transform disabled:opacity-50 disabled:scale-100">
              {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Sparkles size={20} />}
              <span className="hidden md:inline">{isLoading ? "Agent Thinking..." : "Synthesize"}</span>
            </button>
          </form>
          {error && <p className="text-red-400 text-sm mt-4 text-center max-w-4xl mx-auto">{error}</p>}
      </div>

      <div className="flex-grow p-6 md:p-12 pb-24 h-full overflow-y-auto">
        {!reviewData && !isLoading && (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-40 mt-24">
            <Brain size={80} className="mb-6 text-primary" />
            <h1 className="text-4xl font-serif italic mb-4">Awaiting your command.</h1>
            <p className="max-w-md">The agent will scrape live web reviews, databases, and streaming availability.</p>
          </div>
        )}

        <AnimatePresence>
          {reviewData && !isLoading && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-6xl mx-auto space-y-12">
              <div className="flex flex-col md:flex-row gap-8 items-end border-b border-white/5 pb-10">
                {reviewData.metadata?.poster_url && (
                  <img src={reviewData.metadata.poster_url} alt="Poster" className="w-48 md:w-64 rounded-xl shadow-2xl shadow-primary/20 object-cover" />
                )}
                <div className="space-y-4">
                  <h1 className="text-5xl md:text-7xl font-serif italic text-white flex gap-4 flex-wrap">{reviewData.metadata?.title}</h1>
                  <p className="text-lg text-on-surface-variant font-medium">
                    {reviewData.metadata?.release_year} • {reviewData.metadata?.director}
                  </p>
                  <p className="text-2xl pt-2 font-serif leading-relaxed text-white">"{reviewData.synthesis?.verdict}"</p>
                  <button onClick={handleAddWatchlist} disabled={addedWatchlist} className="mt-4 px-6 py-2 bg-white/10 hover:bg-white/20 text-white rounded-full flex gap-2 items-center transition-colors">
                    {addedWatchlist ? <Check size={18}/> : <Plus size={18}/>}
                    {addedWatchlist ? "Saved to Watchlist" : "Add to Watchlist"}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
                <MetricCard label="Reelogue AI Score" score={reviewData.synthesis?.reelogue_rating} total="10" icon={Brain} colorClass="text-primary neon-glow" />
                <MetricCard label="IMDb" score={reviewData.synthesis?.scores?.imdb?.split('/')[0]} total="10" icon={Star} colorClass="text-yellow-500" />
                <MetricCard label="Rotten Tomatoes" score={reviewData.synthesis?.scores?.rotten_tomatoes_critics?.replace('%','')} total="%" icon={TrendingUp} colorClass="text-red-500" />
                <MetricCard label="Metacritic" score={reviewData.synthesis?.scores?.metacritic?.split('/')[0]} total="100" icon={BarChart3} colorClass="text-green-500" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-12 gap-8 pt-8">
                <div className="md:col-span-8 space-y-8">
                  <div className="bg-surface-container-low p-8 rounded-3xl border border-white/5">
                    <h3 className="text-2xl font-serif italic mb-6 text-tertiary">Critical Summary</h3>
                    <p className="text-lg leading-relaxed text-zinc-300">{reviewData.synthesis?.summary}</p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-surface-container-high p-6 rounded-2xl">
                      <h4 className="text-sm uppercase tracking-widest text-primary font-bold mb-4">Best For</h4>
                      <p className="text-sm text-zinc-300">{reviewData.synthesis?.best_for}</p>
                    </div>
                    <div className="bg-surface-container-high p-6 rounded-2xl">
                      <h4 className="text-sm uppercase tracking-widest text-zinc-500 font-bold mb-4">Skip If</h4>
                      <p className="text-sm text-zinc-300">{reviewData.synthesis?.avoid_if}</p>
                    </div>
                  </div>
                </div>

                <div className="md:col-span-4 space-y-6">
                  <div className="p-6 rounded-3xl bg-gradient-to-br from-surface-container-high to-background border border-tertiary/20">
                    <h3 className="font-serif italic text-xl text-tertiary mb-4">Taste Match Note</h3>
                    <p className="text-sm text-zinc-300 italic">{reviewData.synthesis?.taste_match_note}</p>
                  </div>
                  <div className="bg-surface-container-low p-6 rounded-3xl border border-white/5 space-y-4">
                    <h4 className="text-sm uppercase tracking-widest text-on-surface-variant font-bold">Where to Watch</h4>
                    <p className="text-sm text-zinc-300">{reviewData.streaming_raw}</p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}

// -------------------------------------------------------------
// WATCHLIST TAB
// -------------------------------------------------------------
function WatchlistTab() {
  const [watchlist, setWatchlist] = useState<any[]>([]);

  useEffect(() => {
    fetch(`/watchlist/${SESSION_ID}`)
      .then(r => r.json())
      .then(d => setWatchlist(d.watchlist || []));
  }, []);

  const removeMovie = async (title: string) => {
    await fetch(`/watchlist/${SESSION_ID}/${encodeURIComponent(title)}`, { method: "DELETE" });
    setWatchlist(watchlist.filter(w => w.title !== title));
  };

  return (
    <div className="p-12 h-screen overflow-y-auto">
      <h1 className="text-4xl font-serif italic mb-8">My Watchlist.</h1>
      {watchlist.length === 0 ? (
        <p className="text-zinc-500">Your watchlist is empty. Go to Discover to add some!</p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
          {watchlist.map(movie => (
            <div key={movie.id} className="group relative bg-surface-container-low border border-white/5 rounded-xl overflow-hidden hover:border-primary/50 transition-colors">
              <img src={movie.poster_url || "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&q=80"} alt={movie.title} className="w-full h-64 object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
              <div className="p-4 absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent pt-12">
                <h3 className="font-bold text-white leading-tight">{movie.title}</h3>
                <p className="text-xs text-zinc-400">{movie.year}</p>
              </div>
              <button 
                onClick={() => removeMovie(movie.title)}
                className="absolute top-2 right-2 bg-black/60 p-2 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500/80"
              >
                <Plus className="rotate-45" size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// MY REVIEWS TAB
// -------------------------------------------------------------
function MyReviewsTab() {
  const [reviews, setReviews] = useState<any[]>([]);
  const [newReview, setNewReview] = useState({ title: "", rating: 8, feedback: "" });

  useEffect(() => {
    fetch(`/user_reviews/${SESSION_ID}`)
      .then(r => r.json())
      .then(d => setReviews(d.reviews || []));
  }, []);

  const submitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newReview.title) return;
    await fetch("/user_reviews", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: SESSION_ID, ...newReview })
    });
    setReviews([{ ...newReview, created_at: new Date().toISOString() }, ...reviews]);
    setNewReview({ title: "", rating: 8, feedback: "" });
  };

  return (
    <div className="p-12 max-w-4xl mx-auto w-full h-screen overflow-y-auto">
      <h1 className="text-4xl font-serif italic mb-8">My Reviews.</h1>
      
      <div className="bg-surface-container-low p-6 rounded-2xl border border-white/5 mb-12">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><Edit3 size={20} className="text-primary"/> Write a Review</h2>
        <form onSubmit={submitReview} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <input type="text" placeholder="Movie Title" value={newReview.title} onChange={e => setNewReview({...newReview, title: e.target.value})} className="w-full bg-zinc-900 border border-white/10 rounded-xl p-3" required />
            <input type="number" placeholder="Rating (0-10)" min="0" max="10" value={newReview.rating} onChange={e => setNewReview({...newReview, rating: Number(e.target.value)})} className="w-full bg-zinc-900 border border-white/10 rounded-xl p-3" required />
          </div>
          <textarea placeholder="What did you think? (This will permanently update your AI taste profile!)" value={newReview.feedback} onChange={e => setNewReview({...newReview, feedback: e.target.value})} className="w-full bg-zinc-900 border border-white/10 rounded-xl p-3 h-24" />
          <button type="submit" className="bg-white/10 hover:bg-white/20 px-6 py-2 rounded-xl font-bold transition-colors">Submit to Database</button>
        </form>
      </div>

      <div className="space-y-4">
        <h2 className="text-2xl font-serif italic text-zinc-500 mb-4">Past Thoughts</h2>
        {reviews.map((r, i) => (
          <div key={i} className="bg-surface-container-high p-6 rounded-2xl border border-white/5">
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-xl font-bold">{r.title}</h3>
              <span className="bg-primary/20 text-primary px-3 py-1 rounded-lg font-bold">{r.rating}/10</span>
            </div>
            <p className="text-zinc-400 italic">"{r.review_text || r.feedback}"</p>
          </div>
        ))}
        {reviews.length === 0 && <p className="text-zinc-600 italic">No reviews yet.</p>}
      </div>
    </div>
  );
}
