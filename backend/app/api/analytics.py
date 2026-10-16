"""
Analytics routes — dashboard metrics and AI performance stats.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.ticket import Ticket, Conversation, Message
from app.schemas.schemas import AnalyticsOverview

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(db: Session = Depends(get_db)):
    total = db.query(func.count(Ticket.id)).scalar() or 0
    open_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status == "open").scalar() or 0
    ai_resolved = db.query(func.count(Ticket.id)).filter(Ticket.status == "ai_resolved").scalar() or 0
    human_resolved = db.query(func.count(Ticket.id)).filter(Ticket.status == "human_resolved").scalar() or 0
    escalated = db.query(func.count(Ticket.id)).filter(Ticket.status == "escalated").scalar() or 0
    total_convos = db.query(func.count(Conversation.id)).scalar() or 0
    total_msgs = db.query(func.count(Message.id)).scalar() or 0

    ai_rate = (ai_resolved / total * 100) if total > 0 else 0
    esc_rate = (escalated / total * 100) if total > 0 else 0

    return AnalyticsOverview(
        total_tickets=total,
        open_tickets=open_tickets,
        ai_resolved=ai_resolved,
        human_resolved=human_resolved,
        escalated=escalated,
        avg_resolution_time_minutes=3.2,  # Placeholder; in production, calculate from timestamps
        ai_resolution_rate=round(ai_rate, 1),
        escalation_rate=round(esc_rate, 1),
        total_conversations=total_convos,
        total_messages=total_msgs,
    )


@router.get("/tickets/by-status")
def tickets_by_status(db: Session = Depends(get_db)):
    results = db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    return {status: count for status, count in results}


@router.get("/tickets/by-priority")
def tickets_by_priority(db: Session = Depends(get_db)):
    results = db.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
    return {priority: count for priority, count in results}
