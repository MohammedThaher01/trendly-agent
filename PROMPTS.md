# Prompt Engineering Iteration Log

## Version 1: The Basic Persona
**Prompt:** "You are a helpful customer support bot for Trendly. Help users with their orders and returns using the provided tools."
**Result:** The model was too chatty, frequently forgot to check the policy for edge cases, and attempted to collect bank details when users asked for COD refunds.

## Version 2: Adding Guardrails
**Prompt Addition:** "Never ask for bank details. Check the policy carefully. You must use the tools before answering."
**Result:** Better tool usage, but the model struggled with the `lost_in_transit` status, trying to process it as a standard return instead of escalating it.

## Version 3: The Production System Prompt (Final)
To fix these issues, I restructured the prompt to explicitly define core duties, strict rules, and expected behavior around known failure points.

**Key Additions:**
- **Explicit prohibitions:** Added the "NO MANUAL CALCULATIONS" rule to force the model to rely entirely on the Python eligibility tool rather than guessing date differences.
- **Section mapping:** Tied specific behaviors to policy sections (e.g., explicitly referencing Section 1.6 for lost parcels and Section 1.5 for the ₹250 delay credit).
- **Tone enforcement:** "Professional, empathetic, direct, and helpful."

**Final Prompt Excerpt:**
> "NO MANUAL CALCULATIONS: Never calculate date differences or judge eligibility on your own. ALWAYS call `check_return_exchange_eligibility` or `get_order_details`. 
> LOST PARCEL RULE (Section 1.6): If an order status is `lost_in_transit`, DO NOT treat it as a return. Immediately invoke `escalate_to_human`."