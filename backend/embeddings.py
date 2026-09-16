"""
embeddings.py
Generates vector embeddings for document chunks and upserts them into Pinecone.

Uses sentence-transformers (free, runs locally, no extra API key needed) instead of
a paid embedding API — keeps the "completely free" requirement intact.
"""

import hashlib
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

from config import settings
from ingestion import DocumentChunk

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"   # free, local, 384-dim, good enough for a prototype
EMBEDDING_DIM = 384

_model = None
_pinecone_client = None
_index = None


def _get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def _get_pinecone_index():
    global _pinecone_client, _index
    if _index is None:
        _pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)

        existing_indexes = [idx["name"] for idx in _pinecone_client.list_indexes()]
        if settings.PINECONE_INDEX_NAME not in existing_indexes:
            _pinecone_client.create_index(
                name=settings.PINECONE_INDEX_NAME,
                dimension=EMBEDDING_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=settings.PINECONE_ENVIRONMENT),
            )
        _index = _pinecone_client.Index(settings.PINECONE_INDEX_NAME)
    return _index


def embed_text(text: str) -> list[float]:
    model = _get_embedding_model()
    return model.encode(text).tolist()


def _chunk_id(chunk: DocumentChunk) -> str:
    """Deterministic ID so re-ingesting the same chunk overwrites rather than duplicates."""
    raw = f"{chunk.source}-{chunk.chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()


def upsert_chunks(chunks: list[DocumentChunk]) -> int:
    """Embeds and upserts a batch of document chunks into Pinecone. Returns count upserted."""
    if not chunks:
        return 0

    index = _get_pinecone_index()
    vectors = []
    for chunk in chunks:
        vector = embed_text(chunk.text)
        vectors.append({
            "id": _chunk_id(chunk),
            "values": vector,
            "metadata": {"text": chunk.text, "source": chunk.source, "chunk_index": chunk.chunk_index},
        })

    index.upsert(vectors=vectors)
    return len(vectors)
