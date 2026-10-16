"""
Agent Tools — callable functions the AI agent can invoke.
Each tool has a name, description, parameters, and an execute function.
Tools enforce permission boundaries: low-risk tools run immediately,
high-risk tools create human approval requests.
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.ticket import Ticket, Conversation, Message, ApprovalRequest
from app.services.rag_service import search_knowledge
from app.core.config import settings


# ─── Tool Registry ───────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "get_customer",
        "description": "Look up a customer's profile by their customer ID. Returns name, email, phone, address.",
        "parameters": {"customer_id": "integer — the customer's ID"},
        "risk_level": "low",
    },
    {
        "name": "get_customer_orders",
        "description": "Get all orders for a customer. Returns order IDs, statuses, amounts, and dates.",
        "parameters": {"customer_id": "integer — the customer's ID"},
        "risk_level": "low",
    },
    {
        "name": "get_order",
        "description": "Get full details of a specific order including items, status, tracking, and delivery estimate.",
        "parameters": {"order_id": "integer — the order ID"},
        "risk_level": "low",
    },
    {
        "name": "get_order_status",
        "description": "Get the current status and tracking information for an order.",
        "parameters": {"order_id": "integer — the order ID"},
        "risk_level": "low",
    },
    {
        "name": "search_knowledge_base",
        "description": "Search company policies, FAQs, and documentation. Use this when the customer asks about return policies, shipping policies, warranties, or general company information.",
        "parameters": {"query": "string — the search query"},
        "risk_level": "low",
    },
    {
        "name": "create_ticket",
        "description": "Create a new support ticket for an issue that needs tracking.",
        "parameters": {
            "customer_id": "integer — the customer's ID",
            "subject": "string — brief description of the issue",
            "priority": "string — low, medium, high, or critical",
        },
        "risk_level": "low",
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate the current conversation to a human support agent. Use when the issue is too complex, the customer is upset, or you cannot resolve it.",
        "parameters": {"reason": "string — why escalation is needed"},
        "risk_level": "low",
    },
    {
        "name": "cancel_order",
        "description": "Cancel a customer's order. This is a destructive action. Only cancel if the order status is 'processing'. Already shipped orders cannot be cancelled.",
        "parameters": {"order_id": "integer — the order to cancel"},
        "risk_level": "medium",
    },
    {
        "name": "request_refund",
        "description": "Request a refund for an order. High-value refunds require human approval.",
        "parameters": {
            "order_id": "integer — the order to refund",
            "reason": "string — reason for the refund",
        },
        "risk_level": "high",
    },
    {
        "name": "update_shipping_address",
        "description": "Update the shipping address on an order. Only possible if the order hasn't shipped yet.",
        "parameters": {
            "order_id": "integer — the order ID",
            "new_address": "string — the new shipping address",
        },
        "risk_level": "medium",
    },
]


def get_tool_definitions_for_llm() -> list:
    """Return tool definitions formatted for the LLM system prompt."""
    return TOOL_DEFINITIONS


# ─── Tool Implementations ────────────────────────────

def execute_tool(
    tool_name: str,
    args: Dict[str, Any],
    db: Session,
    ticket_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute a tool by name. Returns result dict."""

    if tool_name == "get_customer":
        return _get_customer(db, args.get("customer_id"))

    elif tool_name == "get_customer_orders":
        return _get_customer_orders(db, args.get("customer_id"))

    elif tool_name == "get_order":
        return _get_order(db, args.get("order_id"))

    elif tool_name == "get_order_status":
        return _get_order_status(db, args.get("order_id"))

    elif tool_name == "search_knowledge_base":
        return _search_knowledge_base(db, args.get("query", ""))

    elif tool_name == "create_ticket":
        return _create_ticket(db, args)

    elif tool_name == "escalate_to_human":
        return _escalate_to_human(db, ticket_id, args.get("reason", ""))

    elif tool_name == "cancel_order":
        return _cancel_order(db, args.get("order_id"), ticket_id, conversation_id)

    elif tool_name == "request_refund":
        return _request_refund(db, args.get("order_id"), args.get("reason", ""), ticket_id, conversation_id)

    elif tool_name == "update_shipping_address":
        return _update_shipping_address(db, args.get("order_id"), args.get("new_address", ""), ticket_id, conversation_id)

    else:
        return {"error": f"Unknown tool: {tool_name}"}


# ─── Low-Risk Tools ──────────────────────────────────

def _get_customer(db: Session, customer_id: int) -> dict:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return {"error": f"Customer {customer_id} not found"}
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
    }


def _get_customer_orders(db: Session, customer_id: int) -> dict:
    orders = db.query(Order).filter(Order.customer_id == customer_id).all()
    return {
        "customer_id": customer_id,
        "total_orders": len(orders),
        "orders": [
            {
                "id": o.id,
                "status": o.status,
                "total_amount": o.total_amount,
                "created_at": str(o.created_at) if o.created_at else None,
                "tracking_number": o.tracking_number,
            }
            for o in orders
        ],
    }


def _get_order(db: Session, order_id: int) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": f"Order {order_id} not found"}
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "shipping_address": order.shipping_address,
        "tracking_number": order.tracking_number,
        "estimated_delivery": order.estimated_delivery,
        "created_at": str(order.created_at) if order.created_at else None,
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else "Unknown",
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in order.items
        ],
    }


def _get_order_status(db: Session, order_id: int) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": f"Order {order_id} not found"}
    return {
        "order_id": order.id,
        "status": order.status,
        "tracking_number": order.tracking_number,
        "estimated_delivery": order.estimated_delivery,
        "last_updated": str(order.updated_at) if order.updated_at else None,
    }


def _search_knowledge_base(db: Session, query: str) -> dict:
    results = search_knowledge(db, query, top_k=3)
    if not results:
        return {"results": [], "message": "No relevant documents found"}
    return {
        "results": [
            {
                "title": doc.title,
                "category": doc.category,
                "content": doc.content,
                "relevance_score": round(score, 3),
            }
            for doc, score in results
        ]
    }


def _create_ticket(db: Session, args: dict) -> dict:
    ticket = Ticket(
        customer_id=args["customer_id"],
        subject=args["subject"],
        priority=args.get("priority", "medium"),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return {"ticket_id": ticket.id, "status": "created", "subject": ticket.subject}


def _escalate_to_human(db: Session, ticket_id: Optional[int], reason: str) -> dict:
    if ticket_id:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.status = "escalated"
            ticket.priority = "high"
            db.commit()
    return {
        "escalated": True,
        "ticket_id": ticket_id,
        "reason": reason,
        "message": "This conversation has been escalated to a human support agent.",
    }


# ─── Medium/High-Risk Tools (with safety checks) ─────

def _cancel_order(
    db: Session,
    order_id: int,
    ticket_id: Optional[int],
    conversation_id: Optional[int],
) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": f"Order {order_id} not found"}
    if order.status not in ("processing",):
        return {"error": f"Cannot cancel order with status '{order.status}'. Only 'processing' orders can be cancelled."}

    # Medium risk: execute directly but log
    order.status = "cancelled"
    db.commit()
    return {
        "order_id": order.id,
        "status": "cancelled",
        "message": f"Order #{order.id} has been successfully cancelled.",
    }


def _request_refund(
    db: Session,
    order_id: int,
    reason: str,
    ticket_id: Optional[int],
    conversation_id: Optional[int],
) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": f"Order {order_id} not found"}
    if order.status not in ("delivered", "cancelled"):
        return {"error": f"Cannot refund order with status '{order.status}'. Only 'delivered' or 'cancelled' orders can be refunded."}

    # High-risk check: large refunds require human approval
    if order.total_amount > settings.HIGH_RISK_REFUND_THRESHOLD:
        approval = ApprovalRequest(
            ticket_id=ticket_id or 0,
            conversation_id=conversation_id or 0,
            action_type="request_refund",
            action_payload=json.dumps({
                "order_id": order.id,
                "amount": order.total_amount,
                "reason": reason,
            }),
            risk_level="high",
            status="pending",
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        return {
            "requires_approval": True,
            "approval_request_id": approval.id,
            "order_id": order.id,
            "amount": order.total_amount,
            "message": f"Refund of ${order.total_amount:.2f} requires human agent approval due to high value. A request has been created (#{approval.id}).",
        }

    # Low-value refund: auto-approve
    order.status = "refunded"
    db.commit()
    return {
        "requires_approval": False,
        "order_id": order.id,
        "amount": order.total_amount,
        "status": "refunded",
        "message": f"Refund of ${order.total_amount:.2f} has been processed for order #{order.id}.",
    }


def _update_shipping_address(
    db: Session,
    order_id: int,
    new_address: str,
    ticket_id: Optional[int],
    conversation_id: Optional[int],
) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": f"Order {order_id} not found"}
    if order.status != "processing":
        return {"error": f"Cannot update address for order with status '{order.status}'. Only 'processing' orders can have their address changed."}

    order.shipping_address = new_address
    db.commit()
    return {
        "order_id": order.id,
        "new_address": new_address,
        "message": f"Shipping address for order #{order.id} has been updated.",
    }
