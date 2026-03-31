import json
import os
from typing import Any, Dict

import requests


def _ipfs_add_url() -> str:
    return os.environ.get("IPFS_API_ADD_URL", "http://127.0.0.1:5001/api/v0/add")


def _ipfs_gateway_base() -> str:
    return os.environ.get("IPFS_GATEWAY_URL", "https://ipfs.io/ipfs")


def upload_to_ipfs(data: Dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=True, sort_keys=True).encode("utf-8")
    response = requests.post(
        _ipfs_add_url(),
        files={"file": ("payload.json", payload, "application/json")},
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    cid = body.get("Hash")
    if not cid:
        raise ValueError(f"IPFS add response missing CID: {body}")
    return cid


def fetch_json_from_ipfs(cid: str) -> Dict[str, Any]:
    response = requests.get(f"{_ipfs_gateway_base().rstrip('/')}/{cid}", timeout=30)
    response.raise_for_status()
    return response.json()


def persist_cid_to_filecoin(cid: str) -> Dict[str, Any]:
    return {
        "cid": cid,
        "status": "not_implemented",
        "provider": os.environ.get("FILECOIN_PROVIDER", "none"),
    }
