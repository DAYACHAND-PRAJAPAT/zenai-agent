"""
retriever.py
Queries the Pinecone knowledge base for chunks relevant to a request, and returns
them in the exact shape orchestrator.py expects: [{"text": ..., "source": ...}, ...]

This is the "RAG" half of "RAG + Rules Engine" from the assignment's Core Architecture.
"""

from embeddings import embed_text, _get_pinecone_index


def retrieve_relevant_chunks(query: str, top_k: int = 3) -> list[dict]:
    """
    Returns the top_k most relevant chunks for a query, each with its source document
    name attached — required for the assignment's "source citations" requirement.
    """
    index = _get_pinecone_index()
    query_vector = embed_text(query)

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
    )

    chunks = []
    for match in results.get("matches", []):
        metadata = match.get("metadata", {})
        chunks.append({
            "text": metadata.get("text", ""),
            "source": metadata.get("source", "unknown"),
            "relevance_score": match.get("score", 0.0),
        })

    return chunks
