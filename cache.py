"""
Disk cache for Grok API responses and sentence embeddings.

Responses:  cache/responses.json  — keyed by sha256(model + question)
Embeddings: cache/embeddings.json — keyed by sha256(model_name + text)

Both caches are protected by per-file locks so concurrent threads cannot
corrupt the JSON files during parallel validation runs.
"""
from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

import numpy as np

CACHE_DIR = Path("cache")
_RESP_FILE = CACHE_DIR / "responses.json"
_EMBD_FILE = CACHE_DIR / "embeddings.json"

_resp_lock = threading.Lock()
_embd_lock = threading.Lock()


def _load(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save(path: Path, data: dict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _key(*parts: str) -> str:
    return hashlib.sha256("||".join(parts).encode()).hexdigest()


# ---------------------------------------------------------------------------
# API response cache
# ---------------------------------------------------------------------------

def get_response(model: str, question: str) -> str | None:
    with _resp_lock:
        return _load(_RESP_FILE).get(_key(model, question))


def set_response(model: str, question: str, response: str) -> None:
    with _resp_lock:
        store = _load(_RESP_FILE)
        store[_key(model, question)] = response
        _save(_RESP_FILE, store)


# ---------------------------------------------------------------------------
# Embedding cache
# ---------------------------------------------------------------------------

def get_embedding(model_name: str, text: str) -> np.ndarray | None:
    with _embd_lock:
        store = _load(_EMBD_FILE)
        k = _key(model_name, text)
        if k in store:
            return np.array(store[k], dtype=np.float32)
    return None


def set_embedding(model_name: str, text: str, vector: np.ndarray) -> None:
    with _embd_lock:
        store = _load(_EMBD_FILE)
        store[_key(model_name, text)] = vector.tolist()
        _save(_EMBD_FILE, store)


def clear() -> None:
    """Wipe all cached data (useful when switching models or questions)."""
    with _resp_lock, _embd_lock:
        for f in (_RESP_FILE, _EMBD_FILE):
            if f.exists():
                f.unlink()
    print("Cache cleared.")
