"""
ingestion.py
Loads enterprise documents (PDFs, mock ESG reports, regulatory text) and splits them
into overlapping text chunks ready for embedding. Used by:
  - Document Analysis feature (user-uploaded sustainability/ESG documents)
  - Initial knowledge-base population (mock_documents/ folder)
"""

from dataclasses import dataclass
from pathlib import Path
from pypdf import PdfReader

CHUNK_SIZE = 800        # characters per chunk
CHUNK_OVERLAP = 150     # overlap between consecutive chunks, keeps context continuous


@dataclass
class DocumentChunk:
    text: str
    source: str        # filename or document title
    chunk_index: int


def chunk_text(text: str, source: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[DocumentChunk]:
    """Splits raw text into overlapping chunks. Simple sliding-window approach —
    sufficient for a prototype; a production system might chunk by section/paragraph."""
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    index = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(DocumentChunk(text=chunk, source=source, chunk_index=index))
            index += 1
        start += chunk_size - overlap

    return chunks


def load_pdf(file_path: str) -> str:
    """Extracts raw text from a PDF file."""
    reader = PdfReader(file_path)
    text_parts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(text_parts)


def load_text_file(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")


def ingest_file(file_path: str) -> list[DocumentChunk]:
    """Detects file type, extracts text, and returns ready-to-embed chunks."""
    path = Path(file_path)
    source_name = path.name

    if path.suffix.lower() == ".pdf":
        raw_text = load_pdf(file_path)
    else:
        raw_text = load_text_file(file_path)

    return chunk_text(raw_text, source=source_name)


def ingest_directory(directory: str) -> list[DocumentChunk]:
    """Ingests every supported file in a directory (used to bootstrap the knowledge base
    from backend/data/mock_documents/)."""
    all_chunks = []
    for file_path in Path(directory).glob("*"):
        if file_path.suffix.lower() in (".pdf", ".txt", ".md"):
            all_chunks.extend(ingest_file(str(file_path)))
    return all_chunks
