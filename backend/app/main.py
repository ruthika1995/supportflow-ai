"""
SupportFlow AI — Main FastAPI Application

This is the entry point. It:
1. Creates all database tables
2. Seeds demo data
3. Serves the React frontend (if built)
4. Mounts all API routes
5. Sets up WebSocket endpoints
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.data.seed import seed_database

# Import all models so SQLAlchemy registers them
from app.models.user import User
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.ticket import Ticket, Conversation, Message, ApprovalRequest
from app.models.knowledge import KnowledgeDocument

# Import routers
from app.api.auth import router as auth_router
from app.api.customers import router as customers_router
from app.api.orders import router as orders_router
from app.api.products import router as products_router
from app.api.tickets import router as tickets_router
from app.api.ai import router as ai_router
from app.api.analytics import router as analytics_router
from app.api.websocket import websocket_chat, websocket_agent_feed


# ─── Create App ──────────────────────────────────────

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Customer Support & Operations Platform with Agentic AI, RAG, and Human-in-the-Loop",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Startup ─────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Seed demo data
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


# ─── API Routes ──────────────────────────────────────

app.include_router(auth_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")


# ─── WebSocket Endpoints ─────────────────────────────

@app.websocket("/ws/chat/{conversation_id}/{customer_id}")
async def ws_chat(websocket, conversation_id: int, customer_id: int):
    await websocket_chat(websocket, conversation_id, customer_id)


@app.websocket("/ws/agent/{agent_id}")
async def ws_agent(websocket, agent_id: int):
    await websocket_agent_feed(websocket, agent_id)


# ─── Health Check ────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}


# ─── Serve Frontend ──────────────────────────────────

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
