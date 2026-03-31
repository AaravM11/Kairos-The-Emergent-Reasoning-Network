import hashlib
import json
import os
import ssl
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, Optional, Tuple

# In-process store when KAIROS_FAKE_IPFS=1 (tests / local without daemon)
_FAKE_IPFS_STORE: Dict[str, bytes] = {}


def _use_fake_ipfs() -> bool:
    return os.environ.get("KAIROS_FAKE_IPFS", "").strip() in ("1", "true", "yes")


def _ipfs_add_url() -> str:
    return os.environ.get("IPFS_API_ADD_URL", "http://127.0.0.1:5001/api/v0/add")


def _ipfs_gateway_base() -> str:
    return os.environ.get("IPFS_GATEWAY_URL", "https://ipfs.io/ipfs")


def _storage_backend() -> str:
    return os.environ.get("STORAGE_BACKEND", "kubo").strip().lower()


def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()


def _http_request(
    url: str,
    method: str = "GET",
    data: Optional[bytes] = None,
    headers: Dict[str, str] | None = None,
    timeout: int = 120,
) -> bytes:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for {url}: {detail}") from exc


def _build_multipart_json(filename: str, file_bytes: bytes) -> Tuple[str, bytes]:
    boundary = f"----Kairos{uuid.uuid4().hex}"
    crlf = b"\r\n"
    b = boundary.encode("ascii")
    chunks = [
        b"--" + b + crlf,
        f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode("utf-8") + crlf,
        b"Content-Type: application/json" + crlf,
        crlf,
        file_bytes,
        crlf,
        b"--" + b + b"--" + crlf,
    ]
    body = b"".join(chunks)
    content_type = f"multipart/form-data; boundary={boundary}"
    return content_type, body


def _upload_via_kubo(data: Dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=True, sort_keys=True).encode("utf-8")
    content_type, body = _build_multipart_json("payload.json", payload)
    raw = _http_request(
        _ipfs_add_url(),
        method="POST",
        data=body,
        headers={"Content-Type": content_type},
        timeout=60,
    )
    body_json = json.loads(raw.decode("utf-8"))
    cid = body_json.get("Hash")
    if not cid:
        raise ValueError(f"IPFS add response missing CID: {body_json}")
    return str(cid)


def _upload_via_web3storage(data: Dict[str, Any]) -> str:
    token = os.environ.get("WEB3_STORAGE_TOKEN", "").strip()
    if not token:
        raise ValueError("WEB3_STORAGE_TOKEN is required when STORAGE_BACKEND=web3storage")
    payload = json.dumps(data, ensure_ascii=True, sort_keys=True).encode("utf-8")
    content_type, body = _build_multipart_json("payload.json", payload)
    raw = _http_request(
        "https://api.web3.storage/upload",
        method="POST",
        data=body,
        headers={"Content-Type": content_type, "Authorization": f"Bearer {token}"},
        timeout=120,
    )
    body_json = json.loads(raw.decode("utf-8"))
    cid = body_json.get("cid") or body_json.get("Cid")
    if not cid:
        raise ValueError(f"web3.storage upload response missing cid: {body_json}")
    return str(cid)


def _upload_via_fake(data: Dict[str, Any]) -> str:
    raw = json.dumps(data, ensure_ascii=True, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    fake_cid = f"sha256-{digest}"
    _FAKE_IPFS_STORE[fake_cid] = raw
    return fake_cid


def upload_to_ipfs(data: Dict[str, Any]) -> str:
    if _use_fake_ipfs():
        return _upload_via_fake(data)
    backend = _storage_backend()
    if backend in ("web3storage", "w3storage", "nftstorage"):
        return _upload_via_web3storage(data)
    return _upload_via_kubo(data)


def fetch_json_from_ipfs(cid: str) -> Dict[str, Any]:
    if _use_fake_ipfs():
        raw = _FAKE_IPFS_STORE.get(cid)
        if raw is None:
            raise KeyError(f"Unknown fake IPFS cid: {cid}")
        return json.loads(raw.decode("utf-8"))
    url = f"{_ipfs_gateway_base().rstrip('/')}/{cid}"
    raw = _http_request(url, method="GET", timeout=60)
    return json.loads(raw.decode("utf-8"))


def persist_cid_to_filecoin(cid: str) -> Dict[str, Any]:
    """
    Describe how this CID is persisted and how to reopen it.

    Real Filecoin deals are not made from this stub; we encode the *lane* you are on:
    - web3.storage uploads are Filecoin-backed on their side.
    - Kubo is a local pin (durable only while your node pins / replicates).
    - Fake IPFS is in-memory for tests.
    """
    gateway = f"{_ipfs_gateway_base().rstrip('/')}/{cid}"
    backend = _storage_backend()
    provider = os.environ.get("FILECOIN_PROVIDER", "none").strip()

    if _use_fake_ipfs():
        return {
            "cid": cid,
            "status": "simulated",
            "persistence": "in_process_only",
            "gateway_url": gateway,
            "note": "KAIROS_FAKE_IPFS: CIDs are not on the public network.",
        }

    if backend in ("web3storage", "w3storage", "nftstorage"):
        return {
            "cid": cid,
            "status": "filecoin_backed_pin",
            "persistence": "web3_storage_to_filecoin",
            "provider": "web3.storage",
            "gateway_url": gateway,
            "note": (
                "Uploaded via web3.storage; content is addressed on IPFS and replicated to "
                "Filecoin per their service (no direct deal API in this repo)."
            ),
        }

    if provider and provider.lower() != "none":
        return {
            "cid": cid,
            "status": "delegated",
            "persistence": "custom_provider",
            "provider": provider,
            "gateway_url": gateway,
            "note": "FILECOIN_PROVIDER set; wire a real deal client (Lighthouse, Boost, etc.) to complete storage deals.",
        }

    return {
        "cid": cid,
        "status": "local_ipfs_pin",
        "persistence": "kubo_pin",
        "provider": "kubo",
        "gateway_url": gateway,
        "note": (
            "Pinned on your local IPFS node. For Filecoin-backed durability without running "
            "deals yourself, set STORAGE_BACKEND=web3storage and WEB3_STORAGE_TOKEN."
        ),
    }
