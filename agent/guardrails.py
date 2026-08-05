import re
from typing import Tuple

BANK_PATTERNS = [
    r"\b\d{9,18}\b",                      # Account numbers
    r"\b[A-Z]{4}0[A-Z0-9]{6}\b",          # IFSC codes
    r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", # Credit card
    r"\b\d{3,4}\b"                         # CVV / Pin standalone hints
]

UNAUTHORIZED_OFFERS = [
    r"\b50% off\b", r"\b20% off\b", r"\bdiscount code\b", r"\bfree gift\b"
]

def sanitize_and_validate_output(bot_response: str) -> Tuple[bool, str]:
    """
    Scans LLM output to ensure zero policy violations (Section 7).
    """
    # 1. Check for unauthorized financial collection requests
    if any(keyword in bot_response.lower() for keyword in ["bank account", "account number", "ifsc", "cvv", "card number"]):
        if "never collect" not in bot_response.lower() and "human agent" not in bot_response.lower():
            return False, "I apologize, but for safety reasons, I cannot collect bank or payment details in chat. A support agent will send a secure link to collect COD payout details (Section 3.3)."

    # 2. Check for hallucinated discounts
    for pattern in UNAUTHORIZED_OFFERS:
        if re.search(pattern, bot_response, re.IGNORECASE):
            return False, "I cannot offer promotional discounts outside official policy guidelines. Let me know if you need assistance with store credits for delayed orders."

    return True, bot_response