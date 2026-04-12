try:
    import agents
    from agents import onboarding_agent, recommendation_agent, review_agent, judge_agent
    import tools
    from tools import tmdb_fetch, tavily_search
    import memory
    from memory import user_profile
    print("All imports OK")
except Exception as e:
    print(f"Import failed: {e}")
