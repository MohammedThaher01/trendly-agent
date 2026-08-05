# Solution Note: Trendly Agentic Support Assistant

## Architecture & Approach
The solution uses a hybrid architecture. Instead of relying purely on a Retrieval-Augmented Generation (RAG) approach where an LLM parses the policy and attempts date arithmetic (which is highly prone to hallucinations), this system splits the workload:

1. **Conversational Orchestrator:** The LLM handles natural language understanding, empathetic engagement, and multi-turn state tracking.
2. **Deterministic Rules Engine:** The actual business logic—calculating 30-day windows, checking if an item is a non-returnable category (like jewellery or innerwear), and handling final-sale edge cases—is executed strictly in Python via function calling.
3. **Guardrail Interceptor:** A final validation layer runs a regex check on the LLM's output to guarantee compliance with Section 7 (preventing the collection of bank details or the offering of unauthorized discounts).

## Key Trade-offs
* **Tool Calling vs. Keyword Matching:** Using real tool calling increases latency slightly compared to basic keyword matching, but it enables genuine dynamic reasoning and multi-step execution. 
* **Stateless API vs. Persistent DB:** For this assignment, conversation state is held in memory. In a production setting, this would be swapped for Redis or Postgres to allow horizontal scaling of the FastAPI workers.

## Known Limitations
* The current setup relies on a fixed "current evaluation date" (August 4, 2026) to make date math deterministic against the static `orders.json` file. 
* Token limits are not explicitly managed; exceptionally long multi-turn conversations could theoretically overflow the context window, requiring a summarization pipeline in the future.

## 5 Discovery Questions for Trendly Ops
Before deploying this into production for 2,000 chats/day, I would ask the ops team:

1. **Inventory Synchronization:** How frequently are inventory levels updated in the backend? Is stock reserved immediately when an exchange is approved in chat, or only after the return parcel passes warehouse inspection?
2. **Reverse Logistics:** What is the exact fallback protocol when a customer’s pincode is non-serviceable for reverse pickup? Can the agent issue self-ship instructions automatically, or should those be routed to human agents?
3. **Authentication:** How should the agent authenticate a customer before displaying order details or processing a return to prevent unauthorized data access?
4. **Discretionary Approvals:** What authorization matrix exists for human agents to override hard rules (e.g., approving a return at day 31 for a high-LTV customer)? Should the assistant ever suggest escalation in these specific edge cases?
5. **COD Refunds:** Since chat cannot collect bank details for COD refunds (Section 3.3), what secure third-party form link (e.g., Razorpay payout link) should the assistant send to collect details out-of-band?