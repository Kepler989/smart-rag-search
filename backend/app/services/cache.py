"""
Redis caching service for embeddings and LLM responses.
Uses SHA-256 hash of query text as the cache key.
"""
import hashlib
import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return the singleton Redis client, creating it if needed."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_client


def _make_key(prefix: str, text: str) -> str:
    """Create a namespaced SHA-256 cache key."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"smart_rag:{prefix}:{digest}"


async def get_cached_embedding(query: str) -> list[float] | None:
    """Retrieve a cached embedding vector for the given query text."""
    client = await get_redis()
    key = _make_key("embedding", query)
    try:
        value = await client.get(key)
        if value:
            logger.debug("Cache HIT (embedding): %s", key)
            return json.loads(value)
    except Exception as e:
        logger.warning("Redis get_cached_embedding error: %s", e)
    return None


async def set_cached_embedding(query: str, embedding: list[float]) -> None:
    """Store an embedding vector in the cache."""
    client = await get_redis()
    key = _make_key("embedding", query)
    try:
        await client.setex(key, settings.redis_ttl_seconds, json.dumps(embedding))
        logger.debug("Cache SET (embedding): %s", key)
    except Exception as e:
        logger.warning("Redis set_cached_embedding error: %s", e)


async def get_cached_rag_response(query: str) -> dict[str, Any] | None:
    """Retrieve a cached full RAG response for the given query."""
    client = await get_redis()
    key = _make_key("rag", query)
    try:
        value = await client.get(key)
        if value:
            logger.debug("Cache HIT (rag): %s", key)
            return json.loads(value)
    except Exception as e:
        logger.warning("Redis get_cached_rag_response error: %s", e)
    return None


async def set_cached_rag_response(query: str, response: dict[str, Any]) -> None:
    """Store a full RAG response in the cache."""
    client = await get_redis()
    key = _make_key("rag", query)
    try:
        await client.setex(key, settings.redis_ttl_seconds, json.dumps(response, default=str))
        logger.debug("Cache SET (rag): %s", key)
    except Exception as e:
        logger.warning("Redis set_cached_rag_response error: %s", e)


async def invalidate_document_cache(document_id: str) -> None:
    """Invalidate all cached responses (called after document update/delete)."""
    client = await get_redis()
    try:
        # Invalidate all rag and embedding keys (broad flush for simplicity)
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await client.scan(cursor, match="smart_rag:*", count=100)
            if keys:
                await client.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        logger.info("Invalidated %d cache keys after document change", deleted)
    except Exception as e:
        logger.warning("Redis invalidate_document_cache error: %s", e)


async def close_redis() -> None:
    """Close the Redis connection on app shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
