import json
import pytest
from agent.tools import (
    _normalize_id,
    check_return_exchange_eligibility,
    check_delay_credit_eligibility
)

def test_normalize_id():
    assert _normalize_id("4524") == "TR-4524"
    assert _normalize_id("tr 4524") == "TR-4524"
    assert _normalize_id("order 4524") == "TR-4524"
    assert _normalize_id("TR-4524") == "TR-4524"

def test_return_window_expired():
    # TR-4523 delivered June 5, 2026 -> Past 30 days
    res = json.loads(check_return_exchange_eligibility("TR-4523", "TR-JKT-008", "return"))
    assert res["eligible"] is False
    assert "exceeds" in res["reason"].lower()

def test_non_returnable_category():
    # TR-4527 is jewellery
    res = json.loads(check_return_exchange_eligibility("TR-4527", "TR-EAR-042", "return"))
    assert res["eligible"] is False
    assert "non-returnable" in res["reason"].lower()

def test_final_sale_exchange_only():
    # TR-4528 is Final Sale
    res = json.loads(check_return_exchange_eligibility("TR-4528", "TR-SHR-009", "return"))
    assert res["eligible"] is False
    assert res["allowed_alternative"] == "size_exchange"

def test_delay_credit_eligibility():
    # TR-4525 is delayed by > 3 days
    res = json.loads(check_delay_credit_eligibility("TR-4525"))
    assert res["credit_eligible"] is True
    assert res["credit_amount"] == 250