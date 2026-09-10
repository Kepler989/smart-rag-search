"""
Google Gemini embedding service.
Generates vector embeddings using text-embedding-004 with batching and retry logic.
"""
import asyncio
import logging
from typing import Optional

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client: Optional[genai.Client] = None


def get_genai_client() -> genai.Client:
    """Return the singleton Gemini client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.google_api_key)
    return _client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def embed_text(text: str) -> list[float]:
    """
    Generate a single embedding vector for the given text.
    Uses task_type=RETRIEVAL_DOCUMENT for indexing.
    """
    client = get_genai_client()

    # Run the synchronous call in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: client.models.embed_content(
            model=settings.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=settings.embedding_dimensions,
            ),
        ),
    )
    return result.embeddings[0].values


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def embed_query(text: str) -> list[float]:
    """
    Generate an embedding vector for a search query.
    Uses task_type=RETRIEVAL_QUERY for query-side encoding.
    """
    client = get_genai_client()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: client.models.embed_content(
            model=settings.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=settings.embedding_dimensions,
            ),
        ),
    )
    return result.embeddings[0].values


async def embed_texts_batch(texts: list[str], batch_size: int = 10) -> list[list[float]]:
    """
    Generate embeddings for a list of texts in batches.
    Returns a list of embedding vectors in the same order as the input.
    """
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        logger.info("Embedding batch %d/%d (%d texts)", i // batch_size + 1, (len(texts) - 1) // batch_size + 1, len(batch))

        # Embed each text in the batch concurrently
        tasks = [embed_text(text) for text in batch]
        batch_results = await asyncio.gather(*tasks)
        all_embeddings.extend(batch_results)

        # Small delay between batches to respect rate limits
        if i + batch_size < len(texts):
            await asyncio.sleep(0.1)

    return all_embeddings
