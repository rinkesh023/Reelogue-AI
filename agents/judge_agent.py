import os
import json
import google.generativeai as genai
from memory.user_profile import UserProfile

JUDGE_SYSTEM_PROMPT = """You are Reelogue's ultra-strict, ruthless LLM-as-Judge Auditor.
Your task is to relentlessly evaluate an AI-generated movie review against the user's taste profile. You DO NOT hand out perfect 5/5 scores easily. You actively look for generic writing, missed taste connections, and robotic summaries.

Evaluate the provided review using the following rubric (1-5, where 3 is average, 4 is great, 5 is absolutely flawless):
1. Review Accuracy: Are the scores coherent? Did it accurately summarize the consensus without inventing facts?
2. Recommendation Relevance: Does this actually fit the user's Profile, or is it a generic recommendation?
3. Synthesis Quality: Is the writing actually evocative, punchy, and human-like, or is it boring and robotic?
4. Source Coverage: Did it synthesize multiple review perspectives (IMDb, RT, Metacritic) seamlessly?
5. Personalisation Depth: Did it actively reference the user's specific "Mood" and "Viewing Context", or ignore them entirely?

You must return ONLY a valid JSON dictionary matching this exact structure:
{
  "scores": {
    "review_accuracy": 0,
    "recommendation_relevance": 0,
    "synthesis_quality": 0,
    "source_coverage": 0,
    "personalisation_depth": 0
  },
  "reasoning": {
    "review_accuracy": "Reasoning here...",
    "recommendation_relevance": "Reasoning here...",
    "synthesis_quality": "Reasoning here...",
    "source_coverage": "Reasoning here...",
    "personalisation_depth": "Reasoning here..."
  },
  "overall_score": 0.0,
  "summary": "1-2 sentences summarizing the evaluation.",
  "top_strength": "The best aspect of the review.",
  "top_improvement": "The biggest area for improvement."
}

Return ONLY this strict JSON structure.
"""

def evaluate_review(review_result: dict, profile: UserProfile) -> dict:
    """
    Evaluates the quality of a generated review against a specific rubric using Gemini.
    """
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        system_instruction=JUDGE_SYSTEM_PROMPT,
    )

    evaluation_context = f"""User Profile:
{profile.to_prompt_context()}

Review Output to Evaluate:
{json.dumps(review_result, indent=2)}

Please evaluate the review strictly and provide the JSON output."""

    try:
        response = model.generate_content(evaluation_context)
        raw = response.text.strip()
    except Exception as e:
        raw = json.dumps({
            "scores": {"review_accuracy": 1, "recommendation_relevance": 1, "synthesis_quality": 1, "source_coverage": 1, "personalisation_depth": 1},
            "reasoning": {},
            "overall_score": 1.0,
            "summary": f"GEMINI API ERROR: {str(e)}",
            "top_strength": "N/A",
            "top_improvement": "Fix Gemini limits"
        })

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    try:
        evaluation = json.loads(raw)
        return evaluation
    except json.JSONDecodeError:
        return {
            "scores": {"review_accuracy": 1, "recommendation_relevance": 1, "synthesis_quality": 1, "source_coverage": 1, "personalisation_depth": 1},
            "reasoning": {},
            "overall_score": 1.0,
            "summary": "Failed to parse judge output.",
            "top_strength": "N/A",
            "top_improvement": "Fix parsing"
        }
