import json
import os
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from groq import Groq
from agent.prompts import SYSTEM_PROMPT
from agent.guardrails import sanitize_and_validate_output
from agent.tools import (
    get_order_details,
    check_return_exchange_eligibility,
    check_delay_credit_eligibility,
    load_policy_document,
    escalate_to_human
)

# Load environment variables from the .env file in the project root
load_dotenv()

# Safely fetch the API key and initialize the client
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is missing. Please check your .env file.")

client = Groq(api_key=api_key)

# --- SYSTEM OBSERVABILITY STORE ---
SYSTEM_METRICS = {
    "total_requests": 0,
    "total_prompt_tokens": 0,
    "total_completion_tokens": 0,
    "total_tokens": 0,
    "escalations_count": 0
}

# Tool declarations schema
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Fetch order status, items, carrier tracking, and shipping dates by order ID.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "e.g. TR-4521"}},
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_return_exchange_eligibility",
            "description": "Evaluates Python deterministic logic to check if an item in an order can be returned or exchanged.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "sku": {"type": "string", "description": "SKU identifier e.g. TR-DRS-014"},
                    "action_type": {"type": "string", "enum": ["return", "exchange"]}
                },
                "required": ["order_id", "sku", "action_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_delay_credit_eligibility",
            "description": "Check if an order is delayed past expected delivery by >3 business days for ₹250 store credit.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": "Fetch the official Trendly shipping and returns policy to answer general user questions.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalates chat to a human support agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "conversation_summary": {"type": "string"}
                },
                "required": ["reason", "conversation_summary"]
            }
        }
    }
]

# Session state dictionary: {session_id: [messages]}
SESSION_STORE: Dict[str, List[Dict[str, Any]]] = {}

def sanitize_user_input(text: str) -> str:
    """Masks potential PII (Credit Cards and Phone Numbers) before sending to LLM."""
    # Mask 16 digit card numbers (with or without spaces/dashes)
    cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'
    text = re.sub(cc_pattern, "[MASKED_CARD_NUMBER]", text)

    # Mask Indian phone numbers (10 digits, optional +91)
    phone_pattern = r'\b(?:\+?91[\-\s]?)?[6789]\d{9}\b'
    text = re.sub(phone_pattern, "[MASKED_PHONE_NUMBER]", text)

    return text

def execute_tool(name: str, args: Dict[str, Any]) -> str:
    if name == "get_order_details":
        return get_order_details(args.get("order_id", ""))
    elif name == "check_return_exchange_eligibility":
        return check_return_exchange_eligibility(
            args.get("order_id", ""), 
            args.get("sku", ""), 
            args.get("action_type", "return")
        )
    elif name == "check_delay_credit_eligibility":
        return check_delay_credit_eligibility(args.get("order_id", ""))
    elif name == "search_policy":
        return load_policy_document()
    elif name == "escalate_to_human":
        SYSTEM_METRICS["escalations_count"] += 1
        return escalate_to_human(
            args.get("order_id", ""),
            args.get("reason", ""),
            args.get("conversation_summary", "")
        )
    return json.dumps({"error": "Unknown tool"})

def run_agent_chat(session_id: str, user_message: str) -> str:
    # Mask any PII before we put it into the prompt context
    safe_message = sanitize_user_input(user_message)

    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    messages = SESSION_STORE[session_id]
    messages.append({"role": "user", "content": safe_message})

    MAX_ITERATIONS = 5
    iterations = 0

    while iterations < MAX_ITERATIONS:
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.0
            )
        except Exception as e:
            # Catch Groq Rate Limits / Burst crashes gracefully
            print(f"\n[LLM API ERROR] {str(e)}\n")
            return "I am experiencing high network traffic right now. Please wait a few seconds and try again."

        # Track usage metrics
        if hasattr(response, 'usage') and response.usage:
        # Track usage metrics
            SYSTEM_METRICS["total_prompt_tokens"] += response.usage.prompt_tokens
            SYSTEM_METRICS["total_completion_tokens"] += response.usage.completion_tokens
            SYSTEM_METRICS["total_tokens"] += response.usage.total_tokens
            SYSTEM_METRICS["total_requests"] += 1

        response_msg = response.choices[0].message

        # If the model decides it needs to call a tool
        if response_msg.tool_calls:
            messages.append(response_msg)
            
            for tool_call in response_msg.tool_calls:
                tool_name = tool_call.function.name
                
                # Safely parse arguments in case the LLM hallucinates malformed JSON
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}
                    
                tool_result = execute_tool(tool_name, tool_args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": tool_result
                })
            
            iterations += 1
            continue  # Loop to let the LLM synthesize the tool's response
        else:
            # Model generated final response
            final_text = response_msg.content
            break
    else:
        # Failsafe if it hits the MAX_ITERATIONS limit
        final_text = "I'm experiencing a technical issue processing this request. Let me escalate this to a human agent for you."

    # Guardrail Validation Pass (Section 7 Safety Constraints)
    is_valid, sanitized_text = sanitize_and_validate_output(final_text)
    messages.append({"role": "assistant", "content": sanitized_text})

    return sanitized_text