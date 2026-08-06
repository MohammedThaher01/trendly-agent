import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any

# Fixed evaluation date as per the assignment design
CURRENT_EVAL_DATE = datetime(2026, 8, 4, 10, 0, 0, tzinfo=timezone.utc)
NON_RETURNABLE_CATEGORIES = {"innerwear", "socks", "jewellery", "beauty", "fragrance", "face_masks", "gift_cards"}

def _normalize_id(order_id: str) -> str:
    """Normalizes order IDs handling formats like '4524', 'tr 4524', 'order 4524', 'TR-4524'."""
    if not order_id:
        return ""
    
    # Clean string: uppercase and remove spaces/dashes
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', str(order_id)).upper()
    
    # Strip common leading words like "ORDER"
    if cleaned.startswith("ORDER") and len(cleaned) > 5:
        cleaned = cleaned[5:]
        
    # If the user only gave digits (e.g., '4524'), prepend 'TR'
    if cleaned.isdigit():
        cleaned = f"TR{cleaned}"
        
    # If it starts with TR (e.g., 'TR4524'), format as 'TR-4524' for uniform lookup
    if cleaned.startswith("TR") and len(cleaned) > 2:
        return f"TR-{cleaned[2:]}"
        
    return cleaned

def load_orders_data() -> Dict[str, Any]:
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "orders.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_policy_document() -> str:
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "trendly_policy.md")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def get_order_details(order_id: str) -> str:
    if not order_id:
        return json.dumps({"status": "error", "message": "Order ID is missing."})
        
    data = load_orders_data()
    norm_id = _normalize_id(order_id)
    order = next((o for o in data.get("orders", []) if _normalize_id(o["order_id"]) == norm_id), None)
    
    if not order:
        return json.dumps({"status": "error", "message": f"Order {order_id} not found."})
    
    customer = next((c for c in data.get("customers", []) if c["customer_id"] == order["customer_id"]), {})
    return json.dumps({"order": order, "customer": customer})

def check_return_exchange_eligibility(order_id: str, sku: str, action_type: str = "return") -> str:
    if not order_id or not sku:
        return json.dumps({"eligible": False, "reason": "Order ID or SKU is missing."})
        
    data = load_orders_data()
    norm_id = _normalize_id(order_id)
    order = next((o for o in data.get("orders", []) if _normalize_id(o["order_id"]) == norm_id), None)
    
    if not order:
        return json.dumps({"eligible": False, "reason": f"Order {order_id} not found."})
    
    if order["status"] == "cancelled":
        return json.dumps({
            "eligible": False, 
            "reason": "Order was cancelled prior to fulfillment and already refunded. Returns or exchanges cannot be raised against cancelled orders."
        })
    
    if order["status"] == "lost_in_transit":
        return json.dumps({
            "eligible": False,
            "action_required": "escalate_to_human",
            "reason": "Parcel marked lost in transit by carrier. This is treated as a lost-parcel claim, NOT a return. Must be handled by a human support agent."
        })
        
    if order["status"] in ["in_transit", "partially_shipped"]:
        return json.dumps({
            "eligible": False,
            "reason": "Order has not been fully delivered yet. Returns can only be initiated post-delivery."
        })

    item = next((i for i in order.get("items", []) if i["sku"].upper() == sku.upper()), None)
    if not item:
        return json.dumps({"eligible": False, "reason": f"SKU {sku} is not part of order {order_id}."})

    category = item.get("category", "").lower()
    if category in NON_RETURNABLE_CATEGORIES or "jewellery" in category:
        return json.dumps({
            "eligible": False,
            "reason": f"Item '{item['name']}' belongs to category '{category}' which is strictly non-returnable and non-exchangeable for hygiene and safety reasons."
        })

    if not order.get("delivered_at"):
        return json.dumps({"eligible": False, "reason": "Delivery timestamp missing from order."})
        
    delivered_date = datetime.fromisoformat(order["delivered_at"].replace("Z", "+00:00"))
    days_since_delivery = (CURRENT_EVAL_DATE - delivered_date).days

    if days_since_delivery > 30:
        return json.dumps({
            "eligible": False,
            "reason": f"Item was delivered {days_since_delivery} days ago. This exceeds the strict 30-calendar-day window."
        })

    if item.get("final_sale", False):
        if action_type.lower() == "return":
            return json.dumps({
                "eligible": False,
                "allowed_alternative": "size_exchange",
                "reason": f"Item '{item['name']}' was purchased on Final Sale. It is eligible for size exchange only—no refunds or store credit."
            })
        elif action_type.lower() == "exchange":
            return json.dumps({
                "eligible": True,
                "type": "size_exchange_only",
                "reason": f"Item '{item['name']}' is marked Final Sale and is eligible for a size exchange within the 30-day window."
            })

    return json.dumps({
        "eligible": True,
        "type": action_type,
        "pickup_info": "Free reverse pickup available at serviceable pincodes. Up to 2 pickup attempts.",
        "reason": f"Item is within the {days_since_delivery}-day delivery window and meets all eligibility conditions."
    })

def check_delay_credit_eligibility(order_id: str) -> str:
    if not order_id:
        return json.dumps({"credit_eligible": False, "reason": "Order ID is missing."})
        
    data = load_orders_data()
    norm_id = _normalize_id(order_id)
    order = next((o for o in data.get("orders", []) if _normalize_id(o["order_id"]) == norm_id), None)
    
    if not order or not order.get("expected_delivery"):
        return json.dumps({"credit_eligible": False, "reason": "No valid expected delivery date found."})

    expected_dt = datetime.strptime(order["expected_delivery"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    
    if order["status"] in ["delayed", "in_transit", "partially_shipped"] and CURRENT_EVAL_DATE > expected_dt:
        days_past = (CURRENT_EVAL_DATE - expected_dt).days
        if days_past >= 3:
            return json.dumps({
                "credit_eligible": True,
                "credit_amount": 250,
                "currency": "INR",
                "type": "store_credit",
                "reason": f"Order is {days_past} days past expected delivery date. Qualifies for ₹250 store credit on request."
            })
            
    return json.dumps({"credit_eligible": False, "reason": "Order is not delayed past the 3-business-day threshold."})

def escalate_to_human(order_id: str, reason: str, conversation_summary: str) -> str:
    safe_id = _normalize_id(order_id) if order_id else "GENERAL"
    ticket_payload = {
        "status": "escalated",
        "ticket_id": f"TICK-{safe_id}-HUMAN",
        "order_id": order_id,
        "escalation_reason": reason,
        "summary_for_agent": conversation_summary,
        "human_support_hours": "9:00 AM – 9:00 PM IST, 7 days a week"
    }
    
    # Simulates outbound CRM Webhook to terminal
    print(f"\n[CRM DISPATCH SUCCESS] Created Ticket: {ticket_payload['ticket_id']} | Reason: {reason}\n")
    
    return json.dumps(ticket_payload)