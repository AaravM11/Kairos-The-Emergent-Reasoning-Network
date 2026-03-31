import os
import sys
from typing import Any, Dict, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.llm_client import chat_completion, llm_ready
from validation_nodes.validator_llm_parse import parse_score_0_1, parse_bool_after_keyword, parse_feedback_after_keyword

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
    if not llm_ready(openai_key):
        raise ValueError("Set OPENAI_API_KEY or LLM_PROVIDER=ollama with Ollama running.")

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

    try:
        content = chat_completion([{"role": "user", "content": prompt}], openai_key=openai_key)
    except Exception as e:
        return {
            "vn_type": "LogicalVN",
            "valid": False,
            "score": 0.0,
            "feedback": f"LLM error: {str(e)}",
            "story_protocol": None
        }

    vb = parse_bool_after_keyword(content, "valid")
    score = parse_score_0_1(content)
    feedback = parse_feedback_after_keyword(content)
    if score is None:
        return {
            "vn_type": "LogicalVN",
            "valid": False,
            "score": 0.0,
            "feedback": "Could not parse validator score from LLM output.",
            "story_protocol": None,
        }
    valid = vb if vb is not None else (score >= 0.7)

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
