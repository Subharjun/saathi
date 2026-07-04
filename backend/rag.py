"""Tiny fully-offline RAG over the scheme docs.

Embeds each scheme once at startup with a local Ollama embedding model, then does
cosine top-k at query time. No external vector DB needed for ~dozens of docs.
"""
import json
import os

import numpy as np

from gemma import embed

DATA = os.path.join(os.path.dirname(__file__), "data", "schemes.json")


class SchemeIndex:
    def __init__(self):
        with open(DATA, encoding="utf-8") as f:
            self.schemes = json.load(f)
        self.matrix = None  # lazily built so the server can boot before embeddings warm up

    def build(self):
        vecs = [embed(s["text"]) for s in self.schemes]
        self.matrix = np.array(vecs, dtype="float32")
        self.matrix /= np.linalg.norm(self.matrix, axis=1, keepdims=True) + 1e-9
        return len(self.schemes)

    def search(self, query, k=3):
        if self.matrix is None:
            self.build()
        q = np.array(embed(query), dtype="float32")
        q /= np.linalg.norm(q) + 1e-9
        scores = self.matrix @ q
        top = np.argsort(-scores)[:k]
        return [{**self.schemes[i], "score": float(scores[i])} for i in top]

    def by_id(self, sid):
        return next((s for s in self.schemes if s["id"] == sid), None)


index = SchemeIndex()
