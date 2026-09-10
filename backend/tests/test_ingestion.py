"""Unit tests for document ingestion and text splitting."""
import tempfile
from pathlib import Path
import pytest
from app.services.ingestion import (
    RecursiveCharacterTextSplitter,
    ingest_document,
)


def test_recursive_splitter_basic():
    splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
    text = "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega."
    chunks = splitter.split_text(text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 65  # allows slight variance with word boundary


def test_recursive_splitter_short_text():
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    text = "Short sentence."
    chunks = splitter.split_text(text)
    assert len(chunks) == 1
    assert chunks[0] == "Short sentence."


def test_ingest_markdown_file():
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
        f.write("# Introduction\n\nThis is a test document about RAG architecture.\n\n## Section 2\n\npgvector is awesome.")
        temp_path = Path(f.name)

    try:
        chunks = ingest_document(temp_path, filename="sample.md", chunk_size=200, chunk_overlap=20)
        assert len(chunks) >= 1
        assert chunks[0].metadata["file_type"] == "md"
        assert chunks[0].metadata["filename"] == "sample.md"
    finally:
        temp_path.unlink()


def test_ingest_txt_file():
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("Plain text line 1.\nPlain text line 2.\nPlain text line 3.")
        temp_path = Path(f.name)

    try:
        chunks = ingest_document(temp_path, filename="sample.txt", chunk_size=100, chunk_overlap=10)
        assert len(chunks) >= 1
        assert chunks[0].metadata["file_type"] == "txt"
    finally:
        temp_path.unlink()


def test_ingest_unsupported_file():
    with tempfile.NamedTemporaryFile(suffix=".xyz", mode="w", delete=False) as f:
        f.write("Invalid content")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Unsupported file type"):
            ingest_document(temp_path, filename="test.xyz")
    finally:
        temp_path.unlink()
