import os
import json
import google.generativeai as genai
from memory.user_profile import UserProfile

JUDGE_SYSTEM_PROMPT = """You are Reelogue's strict LLM-as-Judge Evaluator.
Your task is to evaluate the quality of an AI-generated movie review and its relevance to a user's taste profile.

Evaluate the provided review using the following rubric, assigning a score from 1-5 for each criterion:
1. Review Accuracy: Are the aggregated scores (IMDb, RT, Metacritic) factually correct formatting and presented well? 
2. Recommendation Relevance: Does this film genuinely match the user's taste profile? (Use context clues from the profile vs the movie's metadata)
3. Synthesis Quality: Is the AI-written verdict coherent, specific, and non-generic?
4. Source Coverage: Was data retrieved from multiple review sources? (Check for presence of multiple raw_sources/scores)
5. Personalisation Depth: Does the review specifically reference things from the user's profile in the taste_match_note or best_for/avoid_if?

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

Do not include any formatting like ```json or markdown. Provide STRICT evaluation with 1-5 integer scores. Calculate the overall_score as a float average of the 5 criteria."""

def evaluate_review(review_result: dict, profile: UserProfile) -> dict:
    """
    Evaluates the quality of a generated review against a specific rubric.
    """
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=JUDGE_SYSTEM_PROMPT,
    )

    evaluation_context = f"""User Profile:
{profile.to_prompt_context()}

Review Output to Evaluate:
{json.dumps(review_result, indent=2)}

Please evaluate the review strictly and provide the JSON output."""

    response = model.generate_content(evaluation_context)
    raw = response.text.strip()

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
            "scores": {
                "review_accuracy": 1,
                "recommendation_relevance": 1,
                "synthesis_quality": 1,
                "source_coverage": 1,
                "personalisation_depth": 1
            },
            "reasoning": {
                "review_accuracy": "Error parsing LLM response.",
                "recommendation_relevance": "Error parsing LLM response.",
                "synthesis_quality": "Error parsing LLM response.",
                "source_coverage": "Error parsing LLM response.",
                "personalisation_depth": "Error parsing LLM response."
            },
            "overall_score": 1.0,
            "summary": "Failed to parse judge output.",
            "top_strength": "N/A",
            "top_improvement": "Fix parsing"
        }
