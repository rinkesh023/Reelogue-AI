import os
import json
from groq import Groq
from memory.user_profile import UserProfile

ONBOARDING_SYSTEM_PROMPT = """You are Reelogue's friendly onboarding assistant. Your job is to have a short, fun conversation 
to understand the user's film taste. You ask warm, casual questions — not a boring form.

Cover these areas (spread across 5-6 turns max, never dump everything at once):
1. Their name
2. Favourite genres (pick 2-3 they love)
3. A few films or series they absolutely loved — and why
4. Any genres or themes they dislike or want to avoid
5. Current mood / what they feel like watching tonight
6. Viewing context (solo, date night, family, friends)
7. Content type preference (movies, series, or both)
8. Streaming services they have (Netflix, Prime, Disney+, etc.)
9. Language preference (any, English only, open to subtitles)

IMPORTANT: When you have collected enough information (at least 4-5 of the above points), 
end your final message with exactly this JSON block on its own line:
PROFILE_COMPLETE: {"name":"...","favourite_genres":[],"favourite_films":[],"favourite_directors":[],"mood":"...","viewing_context":"...","content_type":"both","language_preference":["English"],"disliked_genres":[],"streaming_services":[]}

Fill in everything you learned. Omit PROFILE_COMPLETE if you still need more info.
Be warm, brief, and cinephile-friendly. Use film references naturally."""

def run_onboarding() -> UserProfile:
    """Run an interactive onboarding conversation and return a filled UserProfile."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    print("\n" + "="*50)
    print("  Welcome to REELOGUE")
    print("="*50 + "\n")

    messages = [
        {"role": "system", "content": ONBOARDING_SYSTEM_PROMPT},
        {"role": "user", "content": "Hello! Start the onboarding conversation."}
    ]

    profile_data = None

    while True:
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages
            )
            reply = response.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            print(f"Error calling Groq: {e}")
            break

        if "PROFILE_COMPLETE:" in reply:
            clean_reply = reply.split("PROFILE_COMPLETE:")[0].strip()
            if clean_reply:
                print(f"\nReelogue: {clean_reply}\n")

            json_str = reply.split("PROFILE_COMPLETE:")[1].strip()
            try:
                profile_data = json.loads(json_str)
            except json.JSONDecodeError:
                pass
            break

        print(f"\nReelogue: {reply}\n")
        user_input = input("You: ").strip()
        if not user_input:
            continue
            
        messages.append({"role": "user", "content": user_input})

    profile = UserProfile()
    if profile_data:
        for key, value in profile_data.items():
            if hasattr(profile, key) and value:
                setattr(profile, key, value)

    print("\n[Profile built! Starting recommendations...]\n")
    return profile
