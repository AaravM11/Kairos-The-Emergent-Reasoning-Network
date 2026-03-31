import os
import sys

import openai
from typing import Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.openai_model import default_chat_model

# === Optional: Story Protocol Integration ===
def register_logic_to_story(reasoning_output: Dict[str, Any]) -> Dict[str, str]:
    """Register logical reasoning path with Story Protocol."""
    print("📜 [Story Protocol] Registered logical reasoning path as reusable IP.")
    return {
        "status": "registered",
        "cid": "ipfs://mockedCID-logical-12345",
        "hash": "0xLOGIC_HASH"
    }

# === LogicalVN with AVS & Story Protocol ===
def run_logical_vn(reasoning_output: Dict[str, Any], openai_key: str, 
                  story_threshold: float = 0.9) -> Dict[str, Any]:
    """
    Validate the logical coherence of reasoning steps.
    
    Args:
        reasoning_output: The output from a reasoning module
        openai_key: OpenAI API key
        story_threshold: Minimum score to register with Story Protocol
        
    Returns:
        Validation result with validity score and feedback
    """
    if not openai_key:
        raise ValueError("OpenAI API key is required for logical validation")
    
    openai.api_key = openai_key

    # Extract reasoning steps and answer
    try:
        reasoning = "\n".join(f"- {step}" for step in reasoning_output["reasoning_steps"])
        answer = reasoning_output["answer"]
    except KeyError as e:
        return {
            "vn_type": "LogicalVN",
            "valid": False,
            "score": 0.0,
            "feedback": f"Missing required field in reasoning output: {e}",
            "story_protocol": None
        }

    # Build prompt for validation
    prompt = f"""
You are a logical validator.

Your task is to evaluate whether the reasoning steps provided below form a coherent logical flow that supports the conclusion.

Reasoning Steps:
{reasoning}

Conclusion:
{answer}

Determine:
1. Does each step follow logically from the last?
2. Are there any contradictions, fallacies, or jumps in logic?
3. Would this pass peer review?

Respond in this format:

Valid: <true|false>
Score: <0-1>
Feedback: <brief explanation>
"""

    # Call OpenAI API
    try:
        response = openai.ChatCompletion.create(
            model=default_chat_model(),
            messages=[{"role": "user", "content": prompt}],
        )
        content = response["choices"][0]["message"]["content"]
    except Exception as e:
        return {
            "vn_type": "LogicalVN",
            "valid": False,
            "score": 0.0,
            "feedback": f"OpenAI API error: {str(e)}",
            "story_protocol": None
        }

    # Parse GPT Output
    try:
        valid = "true" in content.lower().split("valid:")[1].split("\n")[0].strip()
        score = float(content.lower().split("score:")[1].split("\n")[0].strip())
        feedback = content.split("Feedback:")[1].strip()
    except Exception as e:
        return {
            "vn_type": "LogicalVN",
            "valid": False,
            "score": 0.0,
            "feedback": f"Could not parse validator response: {str(e)}",
            "story_protocol": None
        }

    result = {
        "vn_type": "LogicalVN",
        "valid": valid,
        "score": round(score, 2),
        "feedback": feedback,
        "story_protocol": None
    }

    # Story Protocol Trigger (Optional IP registration)
    if valid and score >= story_threshold:
        story_result = register_logic_to_story(reasoning_output)
        result["story_protocol"] = story_result

    return result
