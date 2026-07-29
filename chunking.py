"""Text chunking, shared by ingest.py (full batch) and indexing.py (incremental)."""

def chunk_text(text: str, max_words: int = 200, overlap: int = 30) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text]
    chunks = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
    return chunks