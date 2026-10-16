"""
AI Agent Orchestrator — the core brain of SupportFlow.

This is NOT a simple "user → LLM → answer" pipeline.
The agent follows a ReAct-style loop:

    1. Receive customer message
    2. Understand intent
    3. Determine which tools are needed
    4. Execute tools
    5. Observe results
    6. Reason over results
    7. Respond (or loop back to step 3 if more tools needed)

The agent uses Gemini's function calling to decide which tools to invoke,
and wraps each turn in a structured reasoning loop.
"""
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import httpx
import google.generativeai as genai
from app.core.config import settings
from app.tools.agent_tools import get_tool_definitions_for_llm, execute_tool
from app.models.ticket import Ticket, Conversation, Message, ApprovalRequest
from app.models.customer import Customer


SYSTEM_PROMPT = """You are SupportFlow AI, an intelligent customer support agent for an e-commerce company.

## Your capabilities:
You can look up customer data, check orders, search company policies, create tickets, and perform actions like cancellations and refunds.

## Your tools:
{tools}

## Rules:
1. ALWAYS greet the customer politely.
2. When a customer mentions an order number, use get_order or get_order_status to look it up.
3. For policy questions (returns, shipping, warranties), ALWAYS search the knowledge base first using search_knowledge_base.
4. NEVER make up information. If you don't have data, say so.
5. For cancellations and refunds, ALWAYS check the order status first before attempting the action.
6. If a refund requires human approval, inform the customer that their request has been submitted for review.
7. If the issue is complex or the customer is frustrated, escalate to a human agent.
8. Be concise but helpful. Don't repeat information unnecessarily.

## Tool Calling Format:
When you need to call a tool, respond with a JSON block in this exact format:
```tool_call
{{"tool": "tool_name", "args": {{"param": "value"}}}}
```

You may call multiple tools in sequence. After receiving tool results, reason over them and provide your final response to the customer.
If you don't need any tools, just respond directly.

## Current context:
- Customer ID: {customer_id}
- Customer Name: {customer_name}
"""


def _build_system_prompt(customer_id: int, customer_name: str) -> str:
    tools = get_tool_definitions_for_llm()
    tools_text = "\n".join([
        f"- **{t['name']}**: {t['description']} | Parameters: {t['parameters']} | Risk: {t['risk_level']}"
        for t in tools
    ])
    return SYSTEM_PROMPT.format(
        tools=tools_text,
        customer_id=customer_id,
        customer_name=customer_name,
    )


def _build_conversation_history(messages: List[Message]) -> List[Dict[str, str]]:
    """Convert DB messages to chat history format."""
    history = []
    for msg in messages:
        if msg.sender_type == "customer":
            history.append({"role": "user", "parts": [msg.content]})
        elif msg.sender_type in ("ai_agent", "system"):
            history.append({"role": "model", "parts": [msg.content]})
        elif msg.sender_type == "human_agent":
            history.append({"role": "model", "parts": [f"[Human Agent {msg.sender_name or ''}]: {msg.content}"]})
    return history


def _build_openrouter_history(system_prompt: str, messages: List[Message], current_message: str) -> List[Dict[str, str]]:
    """Convert DB messages to OpenRouter / OpenAI chat format."""
    history = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        if msg.sender_type == "customer":
            history.append({"role": "user", "content": msg.content})
        elif msg.sender_type in ("ai_agent", "system"):
            history.append({"role": "assistant", "content": msg.content})
        elif msg.sender_type == "human_agent":
            history.append({"role": "assistant", "content": f"[Human Agent {msg.sender_name or ''}]: {msg.content}"})
    history.append({"role": "user", "content": current_message})
    return history


def _extract_tool_calls(text: str) -> List[Dict[str, Any]]:
    """Extract tool_call JSON blocks from the LLM response."""
    pattern = r'```tool_call\s*\n?(.*?)\n?```'
    matches = re.findall(pattern, text, re.DOTALL)
    tool_calls = []
    for match in matches:
        try:
            parsed = json.loads(match.strip())
            tool_calls.append(parsed)
        except json.JSONDecodeError:
            continue
    return tool_calls


def _strip_tool_calls(text: str) -> str:
    """Remove tool_call blocks from the response text."""
    pattern = r'```tool_call\s*\n?.*?\n?```'
    cleaned = re.sub(pattern, '', text, flags=re.DOTALL).strip()
    return cleaned


async def run_agent(
    db: Session,
    customer_id: int,
    message: str,
    conversation_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Main agent entry point. Runs the ReAct loop:
    understand → plan → act → observe → respond.

    Returns:
        {
            "response": str,
            "conversation_id": int,
            "ticket_id": int,
            "tool_calls_made": [...],
            "requires_approval": bool,
            "approval_request_id": int | None,
        }
    """
    # 1. Get or create customer context
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return {
            "response": "I'm sorry, I couldn't find your customer profile. Please contact us with your registered email.",
            "conversation_id": 0,
            "ticket_id": 0,
            "tool_calls_made": [],
            "requires_approval": False,
            "approval_request_id": None,
        }

    # 2. Get or create ticket + conversation
    ticket, conversation = _get_or_create_conversation(db, customer_id, conversation_id, message)

    # 3. Save the customer's message
    customer_msg = Message(
        conversation_id=conversation.id,
        sender_type="customer",
        sender_name=customer.name,
        content=message,
    )
    db.add(customer_msg)
    db.commit()

    # 4. Build conversation history
    all_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at).all()

    history = _build_conversation_history(all_messages[:-1])  # Exclude the message we just added

    system_prompt = _build_system_prompt(customer_id, customer.name)

    # 5. Run the ReAct loop (max 5 iterations to prevent infinite loops)
    all_tool_calls = []
    requires_approval = False
    approval_request_id = None
    final_response = ""

    if settings.OPENROUTER_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://supportflow-ai.onrender.com",
                "X-Title": "SupportFlow AI",
                "Content-Type": "application/json",
            }
            client_messages = _build_openrouter_history(system_prompt, all_messages[:-1], message)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response_text = ""
                for iteration in range(5):
                    payload = {
                        "model": settings.OPENROUTER_MODEL,
                        "messages": client_messages,
                        "temperature": 0.2,
                    }
                    resp = await client.post(
                        f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    response_text = data["choices"][0]["message"]["content"]

                    tool_calls = _extract_tool_calls(response_text)
                    if not tool_calls:
                        final_response = _strip_tool_calls(response_text)
                        break

                    tool_results = []
                    for tc in tool_calls:
                        tool_name = tc.get("tool", "")
                        tool_args = tc.get("args", {})
                        result = execute_tool(
                            tool_name, tool_args, db,
                            ticket_id=ticket.id,
                            conversation_id=conversation.id,
                        )
                        all_tool_calls.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result": result,
                        })

                        if result.get("requires_approval"):
                            requires_approval = True
                            approval_request_id = result.get("approval_request_id")

                        tool_results.append(f"Tool '{tool_name}' result: {json.dumps(result)}")

                    client_messages.append({"role": "assistant", "content": response_text})
                    client_messages.append({
                        "role": "user",
                        "content": "Tool results:\n" + "\n".join(tool_results) + "\n\nNow respond to the customer based on these results."
                    })
                else:
                    final_response = _strip_tool_calls(response_text) if response_text else "I apologize, I'm having trouble processing your request. Let me connect you with a human agent."
        except Exception as e:
            print(f"OpenRouter error: {e}, falling back to rule-based engine")
            final_response, all_tool_calls, requires_approval, approval_request_id = _mock_agent_response(
                db, message, customer_id, ticket.id, conversation.id
            )
    elif settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            system_instruction=system_prompt,
        )
        chat = model.start_chat(history=history)

        current_message = message
        for iteration in range(5):
            response = chat.send_message(current_message)
            response_text = response.text

            # Check for tool calls
            tool_calls = _extract_tool_calls(response_text)
            if not tool_calls:
                final_response = response_text
                break

            # Execute tools and collect results
            tool_results = []
            for tc in tool_calls:
                tool_name = tc.get("tool", "")
                tool_args = tc.get("args", {})
                result = execute_tool(
                    tool_name, tool_args, db,
                    ticket_id=ticket.id,
                    conversation_id=conversation.id,
                )
                all_tool_calls.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result,
                })

                # Check if any tool requires approval
                if result.get("requires_approval"):
                    requires_approval = True
                    approval_request_id = result.get("approval_request_id")

                tool_results.append(f"Tool '{tool_name}' result: {json.dumps(result)}")

            # Feed tool results back to the LLM
            current_message = "Tool results:\n" + "\n".join(tool_results) + "\n\nNow respond to the customer based on these results."
        else:
            final_response = _strip_tool_calls(response_text) if response_text else "I apologize, I'm having trouble processing your request. Let me connect you with a human agent."
    else:
        # Fallback when no API key — use a rule-based mock
        final_response, all_tool_calls, requires_approval, approval_request_id = _mock_agent_response(
            db, message, customer_id, ticket.id, conversation.id
        )

    # 6. Save AI response
    ai_msg = Message(
        conversation_id=conversation.id,
        sender_type="ai_agent",
        sender_name="SupportFlow AI",
        content=final_response,
        tool_calls=json.dumps(all_tool_calls) if all_tool_calls else None,
    )
    db.add(ai_msg)

    # 7. Update ticket status
    if requires_approval:
        ticket.status = "in_progress"
    elif any(tc.get("tool") == "escalate_to_human" for tc in all_tool_calls):
        ticket.status = "escalated"
    else:
        ticket.status = "ai_resolved"

    db.commit()

    return {
        "response": final_response,
        "conversation_id": conversation.id,
        "ticket_id": ticket.id,
        "tool_calls_made": all_tool_calls,
        "requires_approval": requires_approval,
        "approval_request_id": approval_request_id,
    }


def _get_or_create_conversation(
    db: Session,
    customer_id: int,
    conversation_id: Optional[int],
    message: str,
) -> Tuple[Ticket, Conversation]:
    """Get existing conversation or create new ticket + conversation."""
    if conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            ticket = db.query(Ticket).filter(Ticket.id == conversation.ticket_id).first()
            return ticket, conversation

    # Create new ticket and conversation
    ticket = Ticket(
        customer_id=customer_id,
        subject=message[:100],
        status="open",
        priority="medium",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    conversation = Conversation(ticket_id=ticket.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return ticket, conversation


def _mock_agent_response(
    db: Session,
    message: str,
    customer_id: int,
    ticket_id: int,
    conversation_id: int,
) -> Tuple[str, List[dict], bool, Optional[int]]:
    """
    Rule-based fallback agent when no Gemini API key is set.
    Demonstrates tool calling without an actual LLM.
    """
    msg_lower = message.lower()
    tool_calls = []
    requires_approval = False
    approval_request_id = None

    # Intent detection — simple keyword matching
    if any(kw in msg_lower for kw in ["order status", "where is my order", "track", "my order", "package", "delayed", "delivery"]):
        # Extract order ID from message
        order_id = _extract_number(message)
        if order_id:
            result = execute_tool("get_order_status", {"order_id": order_id}, db, ticket_id, conversation_id)
            tool_calls.append({"tool": "get_order_status", "args": {"order_id": order_id}, "result": result})
            if "error" in result:
                response = f"I'm sorry, I couldn't find order #{order_id}. Could you double-check the order number?"
            else:
                status = result.get("status", "unknown")
                tracking = result.get("tracking_number", "not available")
                delivery = result.get("estimated_delivery", "not available")
                response = f"I found your order #{order_id}. Here's the current status:\n\n📦 **Status:** {status}\n🔍 **Tracking:** {tracking}\n📅 **Estimated Delivery:** {delivery}\n\nIs there anything else I can help you with?"
        else:
            # Get all customer orders
            result = execute_tool("get_customer_orders", {"customer_id": customer_id}, db, ticket_id, conversation_id)
            tool_calls.append({"tool": "get_customer_orders", "args": {"customer_id": customer_id}, "result": result})
            orders = result.get("orders", [])
            if orders:
                orders_text = "\n".join([f"  • Order #{o['id']} — {o['status']} — ${o.get('total_amount', 0):.2f}" for o in orders[:5]])
                response = f"Here are your recent orders:\n\n{orders_text}\n\nWhich order would you like to know more about?"
            else:
                response = "I don't see any orders on your account. Could you provide your order number?"

    elif any(kw in msg_lower for kw in ["cancel", "cancel order"]):
        order_id = _extract_number(message)
        if order_id:
            result = execute_tool("cancel_order", {"order_id": order_id}, db, ticket_id, conversation_id)
            tool_calls.append({"tool": "cancel_order", "args": {"order_id": order_id}, "result": result})
            if "error" in result:
                response = f"I'm unable to cancel that order: {result['error']}"
            else:
                response = f"✅ {result['message']}"
        else:
            response = "I'd be happy to help you cancel an order. Could you please provide the order number?"

    elif any(kw in msg_lower for kw in ["refund", "money back", "return money"]):
        order_id = _extract_number(message)
        if order_id:
            result = execute_tool("request_refund", {"order_id": order_id, "reason": message}, db, ticket_id, conversation_id)
            tool_calls.append({"tool": "request_refund", "args": {"order_id": order_id, "reason": message}, "result": result})
            requires_approval = result.get("requires_approval", False)
            approval_request_id = result.get("approval_request_id")
            if "error" in result:
                response = f"I'm unable to process that refund: {result['error']}"
            else:
                response = f"💰 {result['message']}"
        else:
            response = "I can help you with a refund. Could you provide the order number?"

    elif any(kw in msg_lower for kw in ["return policy", "can i return", "return", "warranty", "shipping policy", "exchange"]):
        result = execute_tool("search_knowledge_base", {"query": message}, db, ticket_id, conversation_id)
        tool_calls.append({"tool": "search_knowledge_base", "args": {"query": message}, "result": result})
        results = result.get("results", [])
        if results:
            policy_text = results[0]["content"]
            response = f"Based on our company policies:\n\n📋 {policy_text}\n\nIs there anything else you'd like to know?"
        else:
            response = "I apologize, I don't have specific policy information available at the moment. Let me connect you with a support agent who can help."

    elif any(kw in msg_lower for kw in ["change address", "update address", "wrong address", "new address"]):
        order_id = _extract_number(message)
        if order_id:
            # Try to extract an address (simplified)
            response = "I can update the shipping address on your order. Could you please provide the new address?"
        else:
            response = "I can update a shipping address for you. Could you provide the order number and the new address?"

    elif any(kw in msg_lower for kw in ["speak to", "human", "agent", "escalate", "manager", "supervisor"]):
        result = execute_tool("escalate_to_human", {"reason": "Customer requested human agent"}, db, ticket_id, conversation_id)
        tool_calls.append({"tool": "escalate_to_human", "args": {"reason": "Customer requested human agent"}, "result": result})
        response = "🙋 I'm connecting you with a human support agent now. They'll be with you shortly. Thank you for your patience!"

    elif any(kw in msg_lower for kw in ["hi", "hello", "hey", "help"]):
        response = "👋 Hello! Welcome to SupportFlow AI. I'm here to help you with:\n\n• 📦 Order tracking and status\n• 🔄 Returns and refunds\n• 🚚 Shipping information\n• ❌ Order cancellations\n• 📋 Company policies\n\nHow can I assist you today?"

    else:
        # Default: search knowledge base and try to help
        result = execute_tool("search_knowledge_base", {"query": message}, db, ticket_id, conversation_id)
        tool_calls.append({"tool": "search_knowledge_base", "args": {"query": message}, "result": result})
        results = result.get("results", [])
        if results and results[0].get("relevance_score", 0) > 0.5:
            response = f"Based on our information:\n\n{results[0]['content']}\n\nCan I help with anything else?"
        else:
            response = "I'm not quite sure I understand your request. Could you tell me more about what you need help with? I can assist with orders, refunds, returns, shipping, and general questions about our services."

    return response, tool_calls, requires_approval, approval_request_id


def _extract_number(text: str) -> Optional[int]:
    """Extract the first number from a text string (likely an order ID)."""
    numbers = re.findall(r'\d+', text)
    if numbers:
        return int(numbers[0])
    return None
