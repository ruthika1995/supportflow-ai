"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ─── Auth ─────────────────────────────────────────────
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "customer"

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ─── Customer ────────────────────────────────────────
class CustomerCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ─── Product ─────────────────────────────────────────
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    inventory: int = 0
    category: Optional[str] = None

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    inventory: int
    category: Optional[str] = None
    class Config:
        from_attributes = True


# ─── Order ───────────────────────────────────────────
class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    customer_id: int
    status: str
    total_amount: float
    shipping_address: Optional[str] = None
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[str] = None
    items: List[OrderItemOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_id: int
    items: List[dict]  # [{"product_id": 1, "quantity": 2}]
    shipping_address: Optional[str] = None


# ─── Ticket ──────────────────────────────────────────
class TicketCreate(BaseModel):
    customer_id: int
    subject: str
    priority: str = "medium"

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    resolution_notes: Optional[str] = None

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_type: str
    sender_name: Optional[str] = None
    content: str
    tool_calls: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    id: int
    ticket_id: int
    messages: List[MessageOut] = []
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class TicketOut(BaseModel):
    id: int
    customer_id: int
    subject: str
    status: str
    priority: str
    assigned_agent_id: Optional[int] = None
    resolution_notes: Optional[str] = None
    conversations: List[ConversationOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ─── Approval Request ────────────────────────────────
class ApprovalRequestOut(BaseModel):
    id: int
    ticket_id: int
    conversation_id: int
    action_type: str
    action_payload: str
    risk_level: str
    status: str
    reviewed_by: Optional[int] = None
    review_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ApprovalAction(BaseModel):
    status: str  # approved | rejected
    review_notes: Optional[str] = None


# ─── Knowledge Base ──────────────────────────────────
class KnowledgeDocOut(BaseModel):
    id: int
    filename: str
    title: Optional[str] = None
    category: Optional[str] = None
    content: str
    chunk_index: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ─── AI Chat ─────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    customer_id: int
    conversation_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    ticket_id: int
    tool_calls_made: List[dict] = []
    requires_approval: bool = False
    approval_request_id: Optional[int] = None


# ─── Analytics ────────────────────────────────────────
class AnalyticsOverview(BaseModel):
    total_tickets: int
    open_tickets: int
    ai_resolved: int
    human_resolved: int
    escalated: int
    avg_resolution_time_minutes: Optional[float] = None
    ai_resolution_rate: float
    escalation_rate: float
    total_conversations: int
    total_messages: int
