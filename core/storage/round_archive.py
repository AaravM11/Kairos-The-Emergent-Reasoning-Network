"""Append lightweight marketplace round records for in-app archive / replay."""

import json
import os
from typing import Any, Dict, List

DEFAULT_INDEX_PATH = "output/kairos_rounds_index.json"
_MAX_ROUNDS = 200


def _index_path() -> str:
    return os.environ.get("KAIROS_ROUNDS_INDEX_PATH", DEFAULT_INDEX_PATH)


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def append_marketplace_round(record: Dict[str, Any]) -> None:
    """
    Append one record to the local rounds index (JSON). Safe to call after a successful
    orchestrate(); failures here must not break the round.
    """
    path = _index_path()
    _ensure_parent(path)
    rounds: List[Dict[str, Any]] = []
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            if isinstance(data.get("rounds"), list):
                rounds = data["rounds"]
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            rounds = []
    row = dict(record)
    row.setdefault(
        "storage_backend",
        os.environ.get("STORAGE_BACKEND", "kubo").strip().lower(),
    )
    rounds.append(row)
    rounds = rounds[-_MAX_ROUNDS:]
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fp:
        json.dump({"rounds": rounds}, fp, indent=2)
    os.replace(tmp, path)
