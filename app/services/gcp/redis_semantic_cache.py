"""
Redis Semantic Cache — Gate 2 in the query flow.

Checks whether a semantically similar question has already been answered.
Uses Vertex AI embeddings + cosine distance against all cached entries in Redis.

Environment variables:
    REDIS_HOST              — Redis Memorystore private IP (default: 127.0.0.1)
    REDIS_PORT              — Redis port (default: 6379)
    CACHE_DISTANCE_THRESHOLD — Cosine distance threshold (default: 0.15)
    CACHE_TTL               — TTL in seconds (default: 3600 = 1 hour)
"""

import os
import json
import uuid

import numpy as np
import redis
import logfire

from app.services.retrieval.embedding import embed_query

DISTANCE_THRESHOLD = float(os.getenv("CACHE_DISTANCE_THRESHOLD", "0.15"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
KEY_PREFIX = "sem_cache:"

_redis_client = None


def _get_redis() -> redis.Redis:
    """Connect to Redis Memorystore (private IP) or local Redis."""
    global _redis_client
    if _redis_client is None:
        host = os.getenv("REDIS_HOST", "127.0.0.1")
        port = int(os.getenv("REDIS_PORT", "6379"))
        _redis_client = redis.Redis(host=host, port=port, decode_responses=True)
    return _redis_client


def _cosine_distance(a: list[float], b: list[float]) -> float:
    """Compute cosine distance between two vectors. Returns 0.0 for identical vectors."""
    a_arr, b_arr = np.array(a), np.array(b)
    dot = np.dot(a_arr, b_arr)
    norm_product = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm_product == 0:
        return 1.0
    return 1.0 - dot / norm_product


def check_cache(query: str) -> str | None:
    """
    Returns cached answer if a semantically similar query exists in Redis.

    Scans all sem_cache:* keys, computes cosine distance between the query
    embedding and each cached embedding. Returns the answer from the closest
    match if distance < DISTANCE_THRESHOLD.
    """
    try:
        r = _get_redis()
        query_vec = embed_query(query)

        best_distance = float("inf")
        best_answer = None

        for key in r.scan_iter(f"{KEY_PREFIX}*"):
            raw = r.get(key)
            if raw is None:
                continue
            entry = json.loads(raw)
            cached_vec = entry["embedding"]
            distance = _cosine_distance(query_vec, cached_vec)

            if distance < best_distance:
                best_distance = distance
                best_answer = entry["answer"]

        if best_distance < DISTANCE_THRESHOLD and best_answer is not None:
            logfire.info(
                "⚡ Semantic Cache HIT — distance={distance:.4f}",
                distance=best_distance,
            )
            return best_answer

        logfire.info(
            "🔍 Semantic Cache MISS — best_distance={distance:.4f}",
            distance=best_distance if best_distance != float("inf") else -1.0,
        )
        return None

    except redis.ConnectionError as e:
        logfire.warning("Redis connection failed, skipping cache: {error}", error=str(e))
        return None
    except Exception as e:
        logfire.error("Semantic cache check error: {error}", error=str(e))
        return None


def store_cache(query: str, answer: str) -> None:
    """
    Stores the query embedding + answer in Redis with TTL.

    Key format: sem_cache:{uuid4}
    Value: JSON with 'embedding' (list[float]) and 'answer' (str)
    """
    try:
        r = _get_redis()
        query_vec = embed_query(query)

        cache_key = f"{KEY_PREFIX}{uuid.uuid4()}"
        payload = json.dumps({"embedding": query_vec, "answer": answer})
        r.setex(cache_key, CACHE_TTL, payload)

        logfire.info("📦 Cached answer under key={key}", key=cache_key)

    except redis.ConnectionError as e:
        logfire.warning("Redis connection failed, skipping store: {error}", error=str(e))
    except Exception as e:
        logfire.error("Semantic cache store error: {error}", error=str(e))
