"""
RAG (Retrieval-Augmented Generation) service.
Handles document ingestion, embedding, and semantic search.
Uses Gemini embeddings and cosine similarity over JSON-stored vectors (SQLite compatible).
"""
import json
import numpy as np
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
import google.generativeai as genai
from app.core.config import settings
from app.models.knowledge import KnowledgeDocument


def _get_embedding(text: str) -> List[float]:
    """Generate embedding vector using Gemini."""
    if not settings.GEMINI_API_KEY:
        # Return a zero vector as fallback when no API key is configured
        return [0.0] * 768
    genai.configure(api_key=settings.GEMINI_API_KEY)
    result = genai.embed_content(
        model=settings.GEMINI_EMBED_MODEL,
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    dot = np.dot(a_arr, b_arr)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0:
        return 0.0
    return float(dot / norm)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks by words."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
    return chunks if chunks else [text]


def ingest_document(
    db: Session,
    filename: str,
    content: str,
    title: Optional[str] = None,
    category: Optional[str] = None,
) -> List[KnowledgeDocument]:
    """Chunk a document, embed each chunk, and store in the database."""
    chunks = chunk_text(content)
    docs = []
    for i, chunk in enumerate(chunks):
        embedding = _get_embedding(chunk)
        doc = KnowledgeDocument(
            filename=filename,
            title=title or filename,
            category=category,
            content=chunk,
            chunk_index=i,
            embedding=json.dumps(embedding),
        )
        db.add(doc)
        docs.append(doc)
    db.commit()
    for doc in docs:
        db.refresh(doc)
    return docs


def search_knowledge(
    db: Session,
    query: str,
    top_k: int = 3,
    category: Optional[str] = None,
) -> List[Tuple[KnowledgeDocument, float]]:
    """Semantic search over the knowledge base. Returns (doc, score) pairs."""
    query_embedding = _get_embedding(query)

    # Fetch all documents (for SQLite; with pgvector you'd do this in SQL)
    q = db.query(KnowledgeDocument).filter(KnowledgeDocument.embedding.isnot(None))
    if category:
        q = q.filter(KnowledgeDocument.category == category)
    all_docs = q.all()

    scored = []
    for doc in all_docs:
        doc_embedding = json.loads(doc.embedding)
        score = _cosine_similarity(query_embedding, doc_embedding)
        scored.append((doc, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
