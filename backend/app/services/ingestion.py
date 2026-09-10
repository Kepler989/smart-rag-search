"""
Document ingestion and chunking pipeline.
Supports PDF, Markdown, and TXT files with recursive character text splitting.
"""
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """A single text chunk with associated metadata."""
    content: str
    chunk_index: int
    page_number: int | None = None
    section: str | None = None
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Recursive Character Text Splitter
# ---------------------------------------------------------------------------

class RecursiveCharacterTextSplitter:
    """
    Splits text recursively using a hierarchy of separators.
    Mimics LangChain's RecursiveCharacterTextSplitter logic.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text with the given separator hierarchy."""
        final_chunks: list[str] = []
        separator = separators[-1]

        for sep in separators:
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                break

        splits = text.split(separator) if separator else list(text)

        good_splits: list[str] = []
        for split in splits:
            if len(split) < self.chunk_size:
                good_splits.append(split)
            else:
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []
                remaining_seps = separators[separators.index(separator) + 1:]
                if remaining_seps:
                    final_chunks.extend(self._split_text(split, remaining_seps))
                else:
                    final_chunks.append(split)

        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)

        return final_chunks

    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        """Merge small splits into chunks respecting chunk_size and overlap."""
        docs: list[str] = []
        current: list[str] = []
        current_len = 0

        for split in splits:
            split_len = len(split)
            if current_len + split_len + (len(separator) if current else 0) > self.chunk_size:
                if current:
                    doc = separator.join(current).strip()
                    if doc:
                        docs.append(doc)
                    # Trim from front to maintain overlap
                    while current and current_len > self.chunk_overlap:
                        removed = current.pop(0)
                        current_len -= len(removed) + len(separator)
            current.append(split)
            current_len += split_len + (len(separator) if len(current) > 1 else 0)

        if current:
            doc = separator.join(current).strip()
            if doc:
                docs.append(doc)

        return docs

    def split_text(self, text: str) -> list[str]:
        """Public entry point — returns a list of text chunk strings."""
        return self._split_text(text, self.separators)


# ---------------------------------------------------------------------------
# File Parsers
# ---------------------------------------------------------------------------

def _parse_pdf(file_path: Path) -> list[tuple[str, int]]:
    """
    Parse a PDF file and return a list of (text, page_number) tuples.
    Uses PyMuPDF (fitz) for better text extraction quality.
    """
    import fitz  # PyMuPDF

    pages: list[tuple[str, int]] = []
    with fitz.open(str(file_path)) as doc:
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text.strip():
                pages.append((text, page_num))
    return pages


def _parse_markdown(file_path: Path) -> list[tuple[str, int | None]]:
    """Parse a Markdown file, stripping HTML tags and returning (text, None)."""
    text = file_path.read_text(encoding="utf-8")
    # Strip HTML tags if any
    text = re.sub(r"<[^>]+>", "", text)
    return [(text, None)]


def _parse_txt(file_path: Path) -> list[tuple[str, int | None]]:
    """Parse a plain text file."""
    text = file_path.read_text(encoding="utf-8")
    return [(text, None)]


# ---------------------------------------------------------------------------
# Main Ingestion Function
# ---------------------------------------------------------------------------

def ingest_document(
    file_path: Path,
    filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> list[TextChunk]:
    """
    Parse a document file and return a list of TextChunk objects.

    Supports: .pdf, .md, .markdown, .txt

    Each chunk carries:
    - content: the text
    - chunk_index: 0-based position
    - page_number: for PDFs
    - section: H1/H2 heading for markdown
    - metadata: filename, file_type, timestamps, etc.
    """
    suffix = file_path.suffix.lower()
    logger.info("Ingesting document: %s (type: %s)", filename, suffix)

    if suffix == ".pdf":
        page_texts = _parse_pdf(file_path)
    elif suffix in (".md", ".markdown"):
        page_texts = _parse_markdown(file_path)
    elif suffix == ".txt":
        page_texts = _parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks: list[TextChunk] = []
    chunk_index = 0
    current_section: str | None = None

    for raw_text, page_number in page_texts:
        # Track markdown headings as section names
        if suffix in (".md", ".markdown"):
            heading_match = re.search(r"^#{1,2}\s+(.+)$", raw_text, re.MULTILINE)
            if heading_match:
                current_section = heading_match.group(1).strip()

        split_texts = splitter.split_text(raw_text)
        for text in split_texts:
            if not text.strip():
                continue
            chunks.append(
                TextChunk(
                    content=text.strip(),
                    chunk_index=chunk_index,
                    page_number=page_number,
                    section=current_section,
                    metadata={
                        "filename": filename,
                        "file_type": suffix.lstrip("."),
                        "chunk_size": len(text),
                    },
                )
            )
            chunk_index += 1

    logger.info("Document '%s' split into %d chunks", filename, len(chunks))
    return chunks
