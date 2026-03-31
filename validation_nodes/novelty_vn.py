import os
import sys
from typing import Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.llm_client import chat_completion, llm_ready
from validation_nodes.validator_llm_parse import parse_score_0_1, parse_bool_after_keyword, parse_feedback_after_keyword

# === Optional: Story Protocol Integration ===
def register_to_story(reasoning_output):
    # Placeholder Story Protocol registration (mocked)
    print("🧠 [Story Protocol] Registered reasoning as IP.")
    return {
        "status": "registered",
        "cid": "ipfs://mockedCID12345",
        "hash": "0xHASHED"
    }

# === Novelty VN with Story Protocol + EigenLayer compatibility ===
def run_novelty_vn(reasoning_output: Any, kg: Any, openai_key: Optional[str], story_threshold: float = 0.85):
    if not llm_ready(openai_key):
        return {
            "vn_type": "NoveltyVN",
            "valid": False,
            "score": 0.0,
            "feedback": "Skipped: set OPENAI_API_KEY or LLM_PROVIDER=ollama with Ollama running.",
            "story_protocol": None,
        }

    # --- Step 1: Extract KG facts as text
    kg_text = "\n".join(
        f"{kg.entities[r.subject_id].label} --{r.predicate}--> {kg.entities[r.object_id].label}"
        for r in kg.relations
    )

    # --- Step 2: Get reasoning steps
    reasoning_steps = reasoning_output.get("reasoning_steps", [])
    reasoning = "\n".join(f"- {step}" for step in reasoning_steps)

    prompt = f"""
You are a novelty evaluator for AI reasoning.

You are given:
Known facts (from the knowledge graph):
{kg_text}

Reasoning steps from an AI module:
{reasoning}

Determine:
1. Does the reasoning combine facts in a new way?
2. Does it introduce any insights that are not already explicitly in the KG?
3. Is the conclusion creative, emergent, or merely obvious?

Respond in this format:

Novel: <true|false>
Score: <0-1>
Feedback: <short explanation>
"""

    content = chat_completion([{"role": "user", "content": prompt}], openai_key=openai_key)

    nb = parse_bool_after_keyword(content, "novel")
    score = parse_score_0_1(content)
    feedback = parse_feedback_after_keyword(content)
    if score is None:
        print("Failed to parse NoveltyVN score from:", content[:200])
        return {
            "vn_type": "NoveltyVN",
            "valid": False,
            "score": 0.0,
            "feedback": "Could not parse validator score from LLM output.",
            "story_protocol": None,
        }
    novel = nb if nb is not None else (score >= 0.7)

    result = {
        "vn_type": "NoveltyVN",
        "valid": novel,
        "score": round(score, 2),
        "feedback": feedback,
        "story_protocol": None  # default
    }

    # --- Step 4: Register with Story Protocol if novel and trustworthy
    if novel and score >= story_threshold:
        story_result = register_to_story(reasoning_output)
        result["story_protocol"] = story_result

    return result
