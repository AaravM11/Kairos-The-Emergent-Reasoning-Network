import os
import sys

import openai

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.openai_model import default_chat_model

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
def run_novelty_vn(reasoning_output, kg, openai_key, story_threshold=0.85):
    openai.api_key = openai_key

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

    response = openai.ChatCompletion.create(
        model=default_chat_model(),
        messages=[{"role": "user", "content": prompt}],
    )

    content = response["choices"][0]["message"]["content"]

    # --- Step 3: Parse LLM output
    try:
        novel = "true" in content.lower().split("novel:")[1].split("\n")[0].strip()
        score = float(content.lower().split("score:")[1].split("\n")[0].strip())
        feedback = content.split("Feedback:")[1].strip()
    except Exception as e:
        print("Failed to parse NoveltyVN output:", e)
        return {
            "vn_type": "NoveltyVN",
            "valid": False,
            "score": 0.0,
            "feedback": "Could not parse validator response.",
            "story_protocol": None
        }

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
