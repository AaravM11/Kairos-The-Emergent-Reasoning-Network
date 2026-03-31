"""Default chat model for legacy openai.ChatCompletion calls (openai package 0.x)."""

import os


def default_chat_model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
