"""Thin client over a LOCAL Ollama server running Gemma 4 — fully offline.

Everything here hits http://localhost:11434. No cloud, no API key.
Set GEMMA_MODEL to the Gemma tag you pulled (e.g. `gemma4`, falls back to `gemma3`).
"""
import base64
import json
import os

import requests

OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "gemma3")          # multimodal chat model
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")  # local embeddings


def chat(messages, tools=None, images=None, fmt=None, temperature=0.2):
    """One Gemma chat turn. `images` = list of base64 strings attached to the last user msg."""
    if images:
        messages = [dict(m) for m in messages]
        messages[-1]["images"] = images
    payload = {
        "model": GEMMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if tools:
        payload["tools"] = tools
    if fmt:
        payload["format"] = fmt  # "json" forces valid-JSON output
    r = requests.post(f"{OLLAMA}/api/chat", json=payload, timeout=300)
    r.raise_for_status()
    return r.json()["message"]


def embed(text):
    r = requests.post(
        f"{OLLAMA}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["embedding"]


def read_image_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def force_json(message):
    """Best-effort parse of a model message into a dict, even if it wraps JSON in prose."""
    content = message.get("content", "").strip()
    try:
        return json.loads(content)
    except Exception:
        start, end = content.find("{"), content.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(content[start : end + 1])
            except Exception:
                pass
    return {"raw": content}
