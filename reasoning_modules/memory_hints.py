"""Shared helpers for biasing reasoning from persistent agent memory scores."""

from typing import Any, Dict, List


def memory_learning_hint(performance_history: List[float]) -> str:
    """
    Short natural-language hint for prompts or conclusion tuning from past scores (0–1 scale).
    """
    if not performance_history:
        return (
            "No prior marketplace rounds for this agent. Prioritize clarity, grounding in facts, "
            "and conservative claims."
        )
    recent = performance_history[-5:]
    avg_recent = sum(recent) / len(recent)
    low = sum(1 for s in recent if s < 0.35)
    high = sum(1 for s in recent if s > 0.65)

    parts = [f"Recent average validation score (last {len(recent)} rounds): {avg_recent:.2f}."]
    if low >= 2:
        parts.append(
            "Several recent low scores: avoid overconfident conclusions; cite graph evidence explicitly "
            "and flag uncertainty."
        )
    if high >= 3:
        parts.append(
            "Strong recent track record: maintain rigor but you may synthesize slightly more confidently "
            "when the graph supports it."
        )
    if avg_recent < 0.4 and low < 2:
        parts.append("Scores trending weak: tighten logic and prefer narrower, well-supported claims.")
    return " ".join(parts)


def memory_context_block(memory_context: Dict[str, Any]) -> str:
    """Structured block for optional injection into module outputs / metrics."""
    memory_context = memory_context or {}
    hist = memory_context.get("performance_history") or []
    if not isinstance(hist, list):
        hist = []
    scores = [float(x) for x in hist if isinstance(x, (int, float))]
    return memory_learning_hint(scores)
