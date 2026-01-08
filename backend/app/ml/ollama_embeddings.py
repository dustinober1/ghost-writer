"""
Helpers for obtaining embeddings from a local Ollama server.
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np
import requests


def get_ollama_embedding(text: str) -> Optional[np.ndarray]:
    """
    Get an embedding vector for the given text from Ollama.

    Uses the /api/embeddings endpoint. Requires:
    - OLLAMA_BASE_URL (default: http://localhost:11434)
    - OLLAMA_EMBEDDING_MODEL or OLLAMA_MODEL (fallback)
    """
    if not text or not text.strip():
        return None

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = (
        os.getenv("OLLAMA_EMBEDDING_MODEL")
        or os.getenv("OLLAMA_MODEL")
        or "llama3.1:8b"
    )

    try:
        resp = requests.post(
            f"{ollama_base_url}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        # Ollama's embeddings API typically returns {"embedding": [...]}.
        embedding = data.get("embedding")
        if embedding is None and "embeddings" in data:
            # Some variants may return a list
            embedding = data["embeddings"][0]

        if embedding is None:
            print("Warning: Ollama embeddings response missing 'embedding' field")
            return None

        vec = np.array(embedding, dtype=float)
        # Normalize to unit vector to be compatible with simple similarity heuristics
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec
    except requests.exceptions.ConnectionError:
        print(
            f"Warning: Cannot connect to Ollama at {ollama_base_url}. "
            "Falling back to stylometric features."
        )
    except requests.exceptions.Timeout:
        print(
            f"Warning: Ollama embeddings request to {ollama_base_url} timed out. "
            "Falling back to stylometric features."
        )
    except Exception as e:
        print(f"Warning: Error getting Ollama embedding: {e}. Falling back to stylometric.")

    return None

