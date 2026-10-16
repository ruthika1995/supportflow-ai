"""
Ticket routes — support ticket management, conversations, messages, approvals.
"""
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ticket import Ticket, Conversation, Message, ApprovalRequest
from app.models.order import Order
from app.schemas.schemas import (
    TicketCreate, TicketUpdate, TicketOut,
    ConversationOut, MessageOut,
    ApprovalRequestOut, ApprovalAction,
)
import json

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("/", response_model=List[TicketOut])
def list_tickets(
    status: str = None,
    priority: str = None,
    db: Session = Depends(get_db),
):
    q = db.query(Ticket)
    if status:
        q = q.filter(Ticket.status == status)
    if priority:
        q = q.filter(Ticket.priority == priority)
    return q.order_by(Ticket.created_at.desc()).all()


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/", response_model=TicketOut)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(**data.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    # Create initial conversation
    conv = Conversation(ticket_id=ticket.id)
    db.add(conv)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/escalate")
def escalate_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "escalated"
    ticket.priority = "high"
    db.commit()
    return {"ticket_id": ticket.id, "status": "escalated"}


@router.post("/{ticket_id}/messages")
def add_message(
    ticket_id: int,
    sender_type: str,
    content: str,
    sender_name: str = None,
    db: Session = Depends(get_db),
):
    """Add a human agent message to a ticket's conversation."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    conv = db.query(Conversation).filter(Conversation.ticket_id == ticket_id).first()
    if not conv:
        conv = Conversation(ticket_id=ticket_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    msg = Message(
        conversation_id=conv.id,
        sender_type=sender_type,
        sender_name=sender_name,
        content=content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return MessageOut.model_validate(msg)


# ─── Approval Requests (Human-in-the-Loop) ──────────

@router.get("/approvals/pending", response_model=List[ApprovalRequestOut])
def list_pending_approvals(db: Session = Depends(get_db)):
    return db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").all()


@router.post("/approvals/{approval_id}/review", response_model=ApprovalRequestOut)
def review_approval(
    approval_id: int,
    action: ApprovalAction,
    db: Session = Depends(get_db),
):
    """Human agent approves or rejects a high-risk action."""
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="This request has already been reviewed")

    approval.status = action.status
    approval.review_notes = action.review_notes
    approval.reviewed_at = datetime.now(timezone.utc)
    db.commit()

    # If approved, execute the action
    if action.status == "approved":
        payload = json.loads(approval.action_payload)
        if approval.action_type == "request_refund":
            order = db.query(Order).filter(Order.id == payload["order_id"]).first()
            if order:
                order.status = "refunded"
                db.commit()

    db.refresh(approval)
    return approval
