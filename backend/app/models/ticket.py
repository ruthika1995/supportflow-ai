"""
Ticket, Conversation, and Message models — support ticket lifecycle.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    subject = Column(String, nullable=False)
    status = Column(String, default="open")  # open | in_progress | ai_resolved | human_resolved | escalated | closed
    priority = Column(String, default="medium")  # low | medium | high | critical
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer")
    assigned_agent = relationship("User")
    conversations = relationship("Conversation", back_populates="ticket", lazy="joined")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("Ticket", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at", lazy="joined")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_type = Column(String, nullable=False)  # customer | ai_agent | human_agent
    sender_name = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)  # JSON string of tools the AI called for this turn
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")


class ApprovalRequest(Base):
    """Human-in-the-loop: high-risk actions require human agent approval."""
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    action_type = Column(String, nullable=False)  # cancel_order | request_refund
    action_payload = Column(Text, nullable=False)  # JSON with action details
    risk_level = Column(String, default="high")  # medium | high
    status = Column(String, default="pending")  # pending | approved | rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    ticket = relationship("Ticket")
