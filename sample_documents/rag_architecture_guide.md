# Retrieval-Augmented Generation (RAG): Architecture & Best Practices

## Introduction
Retrieval-Augmented Generation (RAG) is an architectural pattern that enhances the capabilities of Large Language Models (LLMs) by retrieving relevant information from an external knowledge base before generating a response. This mitigates model hallucinations, ensures up-to-date domain factual correctness, and provides transparent source citations.

## Core Pipeline Architecture

### 1. Document Ingestion & Chunking
Documents (PDFs, Markdown, TXT) are parsed and split into semantically coherent text segments.
- **Chunk Size**: Typically between 500 and 1,500 characters.
- **Chunk Overlap**: Usually 10% to 20% (e.g., 100-200 characters) to preserve contextual continuity across chunk boundaries.
- **Recursive Splitting**: Breaks text hierarchically by paragraphs, sentences, and words rather than arbitrary character offsets.

### 2. Dense Vector Embeddings
Each text chunk is passed through an embedding model such as Google's `text-embedding-004` to produce a high-dimensional vector (e.g., 768 dimensions). The vector represents semantic meaning in continuous latent space:
- Cosine similarity measures angle between normalized vectors: `similarity = (A · B) / (||A|| * ||B||)`.
- Dot product and Euclidean distance (`L2`) are alternative distance metrics.

### 3. Vector Database Indexing (pgvector)
Vectors are indexed using PostgreSQL with the `pgvector` extension.
- **HNSW (Hierarchical Navigable Small World)**: Provides approximate nearest neighbor (ANN) search with logarithmic query complexity O(log N). It constructs a multi-layer graph where greedy routing rapidly converges to nearest vectors.
- **IVFFlat (Inverted File Flat)**: Partitions vectors into Voronoi cells using k-means clustering. Faster build time than HNSW, but lower recall at scale.

### 4. Semantic Search & Context Augmentation
When a user submits a query:
1. The query text is embedded into the same 768-dimensional latent space.
2. An HNSW similarity search retrieves the top-K chunks with cosine distance below a similarity threshold.
3. The retrieved chunks are deduplicated and formatted into a structured context prompt with document IDs, page numbers, and snippet metadata.

### 5. LLM Synthesis & Source Citations
The augmented prompt is fed to a generative model such as `gemini-2.5-flash`. The system prompt instructs the model to:
- Formulate answers strictly grounded in the provided context snippets.
- Include explicit markdown citations `[Doc: filename, Page: X]` referring to source passages.
- Acknowledge when the retrieved context lacks sufficient evidence rather than hallucinating answers.

### 6. Caching Layer (Redis)
To reduce latency and API expenditure:
- **Embedding Cache**: SHA-256 hash of query string mapped to cached vector.
- **RAG Response Cache**: SHA-256 hash of (query + document_corpus_version) mapped to final LLM response and source citations with a configurable TTL (e.g. 1 hour).
