"""Unit tests for cache hashing and latency tracking."""
import hashlib
from app.services.cache import _make_key
from app.middleware.latency import (
    embedding_latency_var,
    vector_search_latency_var,
    llm_latency_var,
)


def test_make_key_deterministic():
    text = "What is Retrieval-Augmented Generation?"
    key1 = _make_key("rag", text)
    key2 = _make_key("rag", text)
    assert key1 == key2
    assert key1.startswith("smart_rag:rag:")
    expected_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert expected_hash in key1


def test_make_key_different_inputs():
    key1 = _make_key("embedding", "query 1")
    key2 = _make_key("embedding", "query 2")
    assert key1 != key2


def test_latency_context_vars():
    embedding_latency_var.set(45.2)
    vector_search_latency_var.set(12.8)
    llm_latency_var.set(180.5)

    assert embedding_latency_var.get() == 45.2
    assert vector_search_latency_var.get() == 12.8
    assert llm_latency_var.get() == 180.5
