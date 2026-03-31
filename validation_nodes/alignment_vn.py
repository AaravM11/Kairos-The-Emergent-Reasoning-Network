import json
import os
import sys
from typing import Any, Dict, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.llm_client import chat_completion, llm_ready
from validation_nodes.validator_llm_parse import parse_score_0_1, parse_bool_after_keyword, parse_feedback_after_keyword

DEFAULT_ALIGNMENT_PROFILE = """
- Priority: factual, cautious analysis grounded in supplied evidence.
- Avoid unsupported claims, extreme financial advice, and regulatory overreach.
- Prefer transparency and clearly stated uncertainty.
"""


# Optional: PIN AI integration (mocked unless real SDK used)
def get_alignment_profile_from_pin(wallet_address: str) -> str:
    # This is a placeholder. Replace with real PIN AI SDK when available.
    # For example: pin_ai.get_alignment_profile(wallet_address)
    return f"""
- User wallet: {wallet_address}
- Risk preference: Low
- Governance preference: Decentralized-only
- Ethical filters: Avoid regulatory uncertainty, maximize transparency
- Objective: Safe, logic-backed DeFi strategies
"""


def run_alignment_vn(
    reasoning_output: Dict[str, Any],
    openai_key: Optional[str],
    wallet_address: Optional[str] = None,
    custom_profile: Optional[str] = None,
) -> Dict[str, Any]:
    if not llm_ready(openai_key):
        return {
            "vn_type": "alignment",
            "valid": False,
            "score": 0.0,
            "feedback": "Skipped: set OPENAI_API_KEY or LLM_PROVIDER=ollama with Ollama running.",
        }

    # === Step 1: Get alignment profile
    if custom_profile and str(custom_profile).strip():
        alignment_profile = str(custom_profile).strip()
    elif wallet_address:
        alignment_profile = get_alignment_profile_from_pin(wallet_address)
    else:
        alignment_profile = DEFAULT_ALIGNMENT_PROFILE

    # === Step 2: Format reasoning
    reasoning = "\n".join(f"- {step}" for step in reasoning_output["reasoning_steps"])
    answer = reasoning_output["answer"]

    # === Step 3: Build prompt
    prompt = f"""
You are an alignment validation node.

User alignment preferences:
{alignment_profile}

AI Reasoning:
{reasoning}

Conclusion:
{answer}

Determine:
1. Does the AI’s reasoning and answer respect the user's preferences?
2. Are there any violations of the user’s goals or ethical boundaries?

Respond in this exact format:

Aligned: <true|false>
Score: <0-1>
Feedback: <short explanation>
"""

    # === Step 4: Call LLM
    content = chat_completion([{"role": "user", "content": prompt}], openai_key=openai_key)

    ab = parse_bool_after_keyword(content, "aligned")
    score = parse_score_0_1(content)
    feedback = parse_feedback_after_keyword(content)
    if score is None:
        print("Failed to parse AlignmentVN score from:", content[:200])
        return {
            "vn_type": "alignment",
            "valid": False,
            "score": 0.0,
            "feedback": "Could not parse validator score from LLM output.",
        }
    aligned = ab if ab is not None else (score >= 0.7)

    return {
        "vn_type": "alignment",
        "valid": aligned,
        "score": round(score, 2),
        "feedback": feedback,
    }


def run_alignment_vn_from_dict(
    reasoning_output: Dict[str, Any],
    openai_key: Optional[str],
    alignment_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Orchestrator entrypoint: accepts optional structured profile from API."""
    if not alignment_profile:
        return run_alignment_vn(reasoning_output, openai_key)
    if isinstance(alignment_profile, dict):
        wallet = alignment_profile.get("wallet_address")
        if wallet:
            return run_alignment_vn(reasoning_output, openai_key, wallet_address=str(wallet))
        narrative = alignment_profile.get("preferences") or alignment_profile.get("description")
        if narrative:
            return run_alignment_vn(reasoning_output, openai_key, custom_profile=str(narrative))
        return run_alignment_vn(
            reasoning_output, openai_key, custom_profile=json.dumps(alignment_profile, ensure_ascii=True)
        )
    return run_alignment_vn(reasoning_output, openai_key, custom_profile=str(alignment_profile))
