"""Embedding generation and storage."""
from __future__ import annotations

import logging
import struct

import numpy as np

from timeline.ai.client import get_backend

logger = logging.getLogger(__name__)


def encode_embedding(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def decode_embedding(data: bytes) -> np.ndarray:
    n = len(data) // 4
    return np.array(struct.unpack(f"{n}f", data), dtype=np.float32)


async def embed_text(text: str) -> bytes | None:
    backend = await get_backend()
    vec = await backend.embed(text[:2000])  # truncate very long texts
    if vec:
        return encode_embedding(vec)
    return None


def cosine_similarity_batch(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between query vector and each row in matrix."""
    query_norm = np.linalg.norm(query)
    if query_norm == 0:
        return np.zeros(len(matrix))
    matrix_norms = np.linalg.norm(matrix, axis=1)
    matrix_norms[matrix_norms == 0] = 1e-10
    return (matrix @ query) / (matrix_norms * query_norm)
