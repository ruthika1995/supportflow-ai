"""
WebSocket handler for real-time support chat.
"""
import json
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.agents.orchestrator import run_agent
from app.core.database import SessionLocal
from typing import Dict, List


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""

    def __init__(self):
        # Maps conversation_id -> list of active WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Maps agent user_id -> WebSocket (for support agents)
        self.agent_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, conversation_id: int):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: int):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id] = [
                ws for ws in self.active_connections[conversation_id] if ws != websocket
            ]

    async def connect_agent(self, websocket: WebSocket, agent_id: int):
        await websocket.accept()
        self.agent_connections[agent_id] = websocket

    def disconnect_agent(self, agent_id: int):
        self.agent_connections.pop(agent_id, None)

    async def send_to_conversation(self, conversation_id: int, message: dict):
        if conversation_id in self.active_connections:
            for ws in self.active_connections[conversation_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    async def broadcast_to_agents(self, message: dict):
        for agent_id, ws in list(self.agent_connections.items()):
            try:
                await ws.send_json(message)
            except Exception:
                self.agent_connections.pop(agent_id, None)


manager = ConnectionManager()


async def websocket_chat(websocket: WebSocket, conversation_id: int, customer_id: int):
    """Handle WebSocket chat for a customer conversation."""
    await manager.connect(websocket, conversation_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            customer_message = message_data.get("message", "")

            # Send typing indicator
            await manager.send_to_conversation(conversation_id, {
                "type": "typing",
                "sender": "ai_agent",
            })

            # Run the AI agent
            db = SessionLocal()
            try:
                result = await run_agent(
                    db=db,
                    customer_id=customer_id,
                    message=customer_message,
                    conversation_id=conversation_id if conversation_id > 0 else None,
                )

                # Send AI response
                await manager.send_to_conversation(conversation_id, {
                    "type": "message",
                    "sender_type": "ai_agent",
                    "sender_name": "SupportFlow AI",
                    "content": result["response"],
                    "tool_calls": result.get("tool_calls_made", []),
                    "requires_approval": result.get("requires_approval", False),
                    "conversation_id": result["conversation_id"],
                    "ticket_id": result["ticket_id"],
                })

                # Notify agents of new/updated ticket
                await manager.broadcast_to_agents({
                    "type": "ticket_update",
                    "ticket_id": result["ticket_id"],
                    "conversation_id": result["conversation_id"],
                })

            finally:
                db.close()

    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)


async def websocket_agent_feed(websocket: WebSocket, agent_id: int):
    """WebSocket feed for support agents — receives real-time ticket updates."""
    await manager.connect_agent(websocket, agent_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Agent sending a message to a conversation
            if message_data.get("type") == "agent_message":
                conv_id = message_data.get("conversation_id")
                content = message_data.get("content", "")
                agent_name = message_data.get("agent_name", "Support Agent")

                # Save to DB
                from app.models.ticket import Message as MessageModel
                db = SessionLocal()
                try:
                    msg = MessageModel(
                        conversation_id=conv_id,
                        sender_type="human_agent",
                        sender_name=agent_name,
                        content=content,
                    )
                    db.add(msg)
                    db.commit()
                finally:
                    db.close()

                # Broadcast to the conversation
                await manager.send_to_conversation(conv_id, {
                    "type": "message",
                    "sender_type": "human_agent",
                    "sender_name": agent_name,
                    "content": content,
                })

    except WebSocketDisconnect:
        manager.disconnect_agent(agent_id)
