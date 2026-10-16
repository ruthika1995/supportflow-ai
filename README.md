# 🛡️ SupportFlow AI — Autonomous Customer Support & Operations Platform

> **Project 2 for Ruthi's AI Portfolio**  
> **Key Concept:** *The AI doesn't just answer questions — it reasons, retrieves company policy via RAG, invokes backend tools, performs permitted database mutations, and routes high-risk actions to human supervisors.*

---

## 🌟 Architecture Overview

SupportFlow AI is an end-to-end full-stack agentic platform designed to bridge autonomous AI support with human operations:

```
[ Customer Message ]
        │
        ▼
[ Agentic ReAct Orchestrator ] ───► [ LLM Intent & Reasoning ]
        │
   ┌────┴──────────────────────────┐
   ▼                               ▼
[ Backend Tools ]           [ RAG Vector Knowledge ]
- get_order_status           - return_policy.md
- cancel_order               - shipping_policy.md
- request_refund             - warranty_policy.md
- search_knowledge_base      - faq.md
   │
   ▼
[ Safety & Guardrail Engine ]
   ├── Low-risk (status check)  ──► Auto-execute & respond to customer
   └── High-risk (refunds >$50) ──► Pause & route to [ Human-in-the-Loop Approval Queue ]
```

---

## 🚀 Key Features

### 1. Dual-Persona Interactive Portal
- **Customer Experience Mode:**
  - Switch between realistic seeded personas (Ruthi, Arun Kumar, Priya Sharma, etc.)
  - Real-time customer order history sidebar with delivery status & tracking codes
  - Interactive chat with live tool execution badges (`get_order_status`, `search_knowledge_base`)
  - One-click prompt chips for rapid testing
- **Operations & Support Desk Mode:**
  - **Live Ticket Dashboard:** Filter by Open, Pending Approval, Escalated, or Resolved
  - **Direct Human Response:** Support agents can reply into ticket threads in real time
  - **Human-in-the-Loop Approval Queue:** Dedicated supervisor desk to approve or reject sensitive actions (refunds, cancellations) with supervisor notes
  - **Orders & Inventory Manager:** Live product catalog with stock counts and customer orders
  - **RAG Knowledge Base:** Indexed policies with an instant vector chunk ingestion form
- **Platform Analytics & Intelligence:**
  - Real-time KPIs: AI Auto-Resolution Rate (~78%), Human Escalation Rate (~12%), Volume Metrics
  - Ticket distribution by Status and Priority
  - Visual ReAct loop architecture breakdown

---

## 🛠️ Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy ORM, SQLite, Pydantic v2
- **Agentic Engine:** ReAct loop with multi-step tool execution + rule-based zero-dependency fallback
- **RAG (Knowledge Base):** Chunking, category filtering, vector similarity search
- **Frontend & Styling:** React 19, TypeScript, Vite, [Impeccable Style System](https://impeccable.style/)
  - **Kinpaku Ink Surfaces:** Deep obsidian canvas (`#0b0d13`), crisp 1px structural borders
  - **Tactile Instrument Controls:** Segmented navigation strip (`ks-instrument-strip`), tactile action buttons
  - **Editorial Typography:** `Albert Sans` + `JetBrains Mono` for high-legibility telemetry and parameters
  - **Zero AI Slop:** Eliminates gratuitous purple gradients, glowing halos, and status-chip soup in favor of purposeful semantic hierarchy
- **Real-Time:** WebSockets for live chat streaming & agent event broadcasts

---

## 🏃 Getting Started

### 1. Run the Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The database auto-creates and seeds on startup.

### 2. Run the Frontend (Dev Server)
```bash
cd frontend
npm run dev
```
Open **`http://localhost:5174/`** (or access the built production app directly at **`http://localhost:8001/`**).

---

## 🎤 Interview Talking Points for Ruthi

1. **Why Agentic AI over simple chatbots?**
   > *"Most support chatbots are just conversational wrappers that hallucinate policies. SupportFlow uses a ReAct pattern where the model determines the action, calls real database APIs, validates conditions, and inspects results before formulating an answer."*

2. **How do you handle dangerous actions (e.g., money loss)?**
   > *"I engineered a Human-in-the-Loop approval gate. When a customer asks for a refund or order cancellation beyond automated limits, the agent doesn't execute the database write. Instead, it generates an approval ticket with risk level tagging and routes it to the operations desk for supervisor authorization."*

3. **How does RAG complement tool calling?**
   > *"Structured data (orders, inventory) lives in relational tables and is accessed via parameterized tools. Unstructured data (warranty rules, return conditions) is stored in the RAG knowledge base. The agent dynamically decides whether to query the database or search vector policy embeddings."*
