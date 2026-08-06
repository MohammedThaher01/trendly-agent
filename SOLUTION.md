# Solution Note: Trendly Agentic Support Assistant

## Architecture Diagram

```text
┌─────────────┐
│  User Chat  │
└──────┬──────┘
       │ 1. Raw Message
       ▼
┌──────────────────────┐
│  Input Guardrails    │  <-- Scrubs PII (Credit Cards, Phone Numbers)
└──────┬───────────────┘
       │ 2. Sanitized Context
       ▼
┌──────────────────────┐  3. Tool Call   ┌───────────────────────────┐
│   LLM Orchestrator   ├────────────────►│  Deterministic Tools      │
│  (Groq / Llama-3.1)  │                 │  (Python Rules Engine)    │
│  - NLU & Routing     │◄────────────────┤   ├─ get_order()          │
│  - Session State     │  4. Tool Result │   ├─ check_eligibility()  │
└──────┬───────────────┘                 │   └─ escalate_to_human()  │
       │ 5. Draft Output                 └───────────────────────────┘
       ▼
┌──────────────────────┐
│  Output Guardrails   │  <-- Blocks Section 7 Violations (Bank Details)
└──────┬───────────────┘
       │ 6. Final Safe Message
       ▼
┌─────────────┐
│  User Chat  │
└─────────────┘
```

## Architecture & Approach
The solution utilizes a hybrid ReAct architecture to eliminate LLM hallucinations on business policies and date math:

1. **Conversational Orchestrator:** The LLM acts purely as a cognitive router, managing natural language understanding, empathetic engagement, and multi-turn state tracking.
2. **Deterministic Rules Engine:** The core business logic—calculating strict 30-day return windows, checking non-returnable categories (e.g., jewellery), and handling final-sale edge cases—is executed entirely in Python via function calling.
3. **Guardrail Interceptor:** Regex-based validation runs on both input (masking PII like credit cards and phone numbers) and output (guaranteeing compliance with Section 7 to prevent unauthorized discounts or bank detail collection).

## Path to Production (Addressing Prototype Trade-offs)
To scale this Proof-of-Concept to handle Trendly's volume of 2,000+ daily chats, the following architectural bottlenecks must be resolved:

1. **Synchronous Execution Bottleneck:** The current FastAPI and Groq client implementations are synchronous. Under high concurrency, this blocks the main thread. Production requires `AsyncGroq` and `async def` routing to prevent request queuing and timeouts.
2. **In-Memory State (Memory Leaks):** Conversation state (`SESSION_STORE`) is currently held in a global Python dictionary. In production, this eventually causes memory leaks and breaks API statelessness. This must be migrated to a Redis cluster to allow horizontal scaling of worker nodes.
3. **Unbounded Context Windows:** The orchestrator currently appends messages indefinitely. Long-lived multi-turn sessions will eventually trigger `400 Token Limit Exceeded` errors. A rolling sliding-window summarizer is required.
4. **Strict LLM Exception Handling:** The current tool parser falls back to empty dictionaries on `json.JSONDecodeError`. A production system needs to feed validation errors back into the LLM context so the agent can self-correct malformed tool calls dynamically.

## 5 Discovery Questions for Trendly Ops
Before deploying this into production, I need the following clarified by the ops team:

1. **Inventory Synchronization:** How frequently are inventory levels updated in the backend? Is stock reserved immediately when an exchange is approved in chat, or only after the return parcel passes warehouse inspection?
2. **Reverse Logistics:** What is the exact fallback protocol when a customer’s pincode is non-serviceable for reverse pickup? Can the agent issue self-ship instructions automatically, or should those be routed to human agents?
3. **Authentication:** How should the agent authenticate a customer before displaying order details or processing a return to prevent unauthorized data access?
4. **Discretionary Approvals:** What authorization matrix exists for human agents to override hard rules (e.g., approving a return at day 31 for a high-LTV customer)? Should the assistant ever suggest escalation in these specific edge cases?
5. **COD Refunds:** Since chat cannot collect bank details for COD refunds (Section 3.3), what secure third-party form link (e.g., Razorpay payout link) should the assistant send to collect details out-of-band?
