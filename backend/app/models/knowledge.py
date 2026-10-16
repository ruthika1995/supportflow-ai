"""
Knowledge document model — RAG knowledge base storage.
Uses simple text + numpy embeddings stored as JSON for SQLite compatibility.
For production PostgreSQL, switch to pgvector.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    title = Column(String, nullable=True)
    category = Column(String, nullable=True)  # faq | policy | product | shipping | warranty
    content = Column(Text, nullable=False)  # Full extracted text
    chunk_index = Column(Integer, default=0)  # Which chunk of the original document
    embedding = Column(Text, nullable=True)  # JSON-serialized float array (SQLite compatible)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
