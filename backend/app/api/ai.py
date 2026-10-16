"""
AI routes — chat endpoint and knowledge base management.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.agents.orchestrator import run_agent
from app.services.rag_service import ingest_document
from app.models.knowledge import KnowledgeDocument
from app.schemas.schemas import ChatRequest, ChatResponse, KnowledgeDocOut

router = APIRouter(prefix="/ai", tags=["AI Agent"])


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(data: ChatRequest, db: Session = Depends(get_db)):
    """
    Main AI support chat endpoint.
    The agent will understand the message, determine needed tools,
    execute them, reason over results, and respond.
    """
    result = await run_agent(
        db=db,
        customer_id=data.customer_id,
        message=data.message,
        conversation_id=data.conversation_id,
    )
    return ChatResponse(**result)


# ─── Knowledge Base Management ────────────────────────

@router.post("/knowledge/upload", response_model=List[KnowledgeDocOut])
async def upload_knowledge(
    file: UploadFile = File(...),
    title: str = Form(None),
    category: str = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a document to the RAG knowledge base."""
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    docs = ingest_document(db, file.filename, text, title, category)
    return docs


@router.post("/knowledge/text", response_model=List[KnowledgeDocOut])
def add_knowledge_text(
    filename: str,
    content: str,
    title: str = None,
    category: str = None,
    db: Session = Depends(get_db),
):
    """Add text content directly to the knowledge base."""
    docs = ingest_document(db, filename, content, title, category)
    return docs


@router.get("/knowledge", response_model=List[KnowledgeDocOut])
def list_knowledge(db: Session = Depends(get_db)):
    return db.query(KnowledgeDocument).all()


@router.delete("/knowledge/{doc_id}")
def delete_knowledge(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"deleted": True, "id": doc_id}
