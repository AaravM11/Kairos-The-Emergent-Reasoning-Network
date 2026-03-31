"""
Unified LLM calls: OpenAI (cloud) or Ollama (local, no API key).

Set LLM_PROVIDER=ollama and run Ollama (https://ollama.com) with a model pulled, e.g.:
  ollama pull llama3.2
Default: LLM_PROVIDER=openai (requires OPENAI_API_KEY).
"""

import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from core.openai_model import default_chat_model


def llm_provider() -> str:
    return os.environ.get("LLM_PROVIDER", "openai").strip().lower()


def llm_ready(openai_key: Optional[str]) -> bool:
    """True if the pipeline can run LLM-backed modules/validators."""
    if llm_provider() == "ollama":
        return True
    return bool(openai_key or os.environ.get("OPENAI_API_KEY"))


def resolve_model(model: Optional[str]) -> str:
    if model and str(model).strip():
        return str(model).strip()
    if llm_provider() == "ollama":
        return os.environ.get("OLLAMA_MODEL", "llama3.2").strip() or "llama3.2"
    return default_chat_model()


def _ollama_chat(messages: List[Dict[str, str]], model: str) -> str:
    host: str = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    url: str = f"{host}/api/chat"
    body: bytes = json.dumps(
        {"model": model, "messages": messages, "stream": False},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=300, context=ctx) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot reach Ollama at {host}. Is `ollama serve` running? ({exc})"
        ) from exc
    data: Dict[str, Any] = json.loads(raw)
    msg = data.get("message") or {}
    content = msg.get("content")
    if not content:
        raise RuntimeError(f"Unexpected Ollama response: {data}")
    return str(content)


def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    openai_key: Optional[str] = None,
) -> str:
    """
    Single user/assistant chat turn; returns assistant text (legacy OpenAI shape abstracted).
    """
    m = resolve_model(model)
    if llm_provider() == "ollama":
        return _ollama_chat(messages, m)

    import openai

    key = openai_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
    openai.api_key = key
    response = openai.ChatCompletion.create(model=m, messages=messages)
    return str(response["choices"][0]["message"]["content"])
