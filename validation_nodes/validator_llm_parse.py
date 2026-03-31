"""Robust parsing of LLM validator replies (markdown / extra prose tolerant)."""

import re
from typing import Optional, Tuple


def parse_bool_after_keyword(text: str, keyword: str) -> Optional[bool]:
    """keyword e.g. 'valid', 'novel', 'aligned' — looks for 'valid: true' style."""
    low = text.lower()
    key = keyword.lower().strip() + ":"
    if key not in low:
        return None
    chunk = low.split(key, 1)[1].split("\n")[0]
    if "true" in chunk:
        return True
    if "false" in chunk:
        return False
    return None


def parse_score_0_1(text: str) -> Optional[float]:
    """
    Extract a score in [0, 1] from phrases like 'Score: 0.85', 'score = .72',
    or '**Score:** 0.6' in markdown.
    """
    low = text.lower()
    m = re.search(r"score\s*[:=]\s*\*?\*?\s*([0-9]+(?:\.[0-9]+)?|\.[0-9]+)", low)
    if not m:
        return None
    try:
        v = float(m.group(1))
    except ValueError:
        return None
    return max(0.0, min(1.0, v))


def parse_feedback_after_keyword(text: str, keyword: str = "feedback") -> str:
    if keyword + ":" not in text and keyword.capitalize() + ":" not in text:
        return text.strip()[:500]
    # Prefer original casing split on Feedback:
    for sep in ("Feedback:", "feedback:"):
        if sep in text:
            return text.split(sep, 1)[1].strip()[:500]
    return text.strip()[:500]


def parse_validator_line_block(content: str, bool_keyword: str) -> Tuple[Optional[bool], Optional[float], str]:
    """Returns (bool_or_none, score_or_none, feedback)."""
    b = parse_bool_after_keyword(content, bool_keyword)
    s = parse_score_0_1(content)
    fb = parse_feedback_after_keyword(content)
    return b, s, fb
