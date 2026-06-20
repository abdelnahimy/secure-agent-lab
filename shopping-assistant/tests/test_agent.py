import pytest
from unittest.mock import MagicMock
from app.tools import (
    redeem_discount_code,
    DISCOUNT_CODES,
)

@pytest.fixture(autouse=True)
def reset_state():
    """Reset the in-memory state before each test to ensure isolation."""
    # Reset discount codes redeemed status
    for code in DISCOUNT_CODES:
        DISCOUNT_CODES[code]["redeemed_by"] = None
    yield

@pytest.fixture
def mock_context():
    """Provides a mocked ToolContext."""
    ctx = MagicMock()
    ctx.state = {}
    return ctx

def test_redeem_valid_code_by_registered_user(mock_context):
    """Business Logic: Registered user can successfully redeem an unused code."""
    result = redeem_discount_code("WELCOME50", "user_001", mock_context)

    assert result["status"] == "success"
    assert result["discount_percent"] == 50
    assert mock_context.state["active_discount"]["code"] == "WELCOME50"
    assert mock_context.state["active_discount"]["user_id"] == "user_001"
    assert DISCOUNT_CODES["WELCOME50"]["redeemed_by"] == "user_001"

def test_security_boundary_unregistered_user(mock_context):
    """Security Boundary: Unregistered users must be blocked from redeeming codes."""
    result = redeem_discount_code("WELCOME50", "unregistered_hacker", mock_context)

    assert result["status"] == "error"
    assert "not a registered user" in result["error"]
    assert "active_discount" not in mock_context.state
    assert DISCOUNT_CODES["WELCOME50"]["redeemed_by"] is None

def test_business_logic_invalid_code(mock_context):
    """Business Logic: Attempting to redeem a non-existent code returns an error."""
    result = redeem_discount_code("NOTREAL20", "user_002", mock_context)

    assert result["status"] == "error"
    assert "not found" in result["error"]
    assert "active_discount" not in mock_context.state

def test_security_boundary_double_redemption(mock_context):
    """Security Boundary: Single-use codes must not be redeemed multiple times."""
    # First redemption by a valid user
    res1 = redeem_discount_code("SUMMER20", "user_001", mock_context)
    assert res1["status"] == "success"

    # Second redemption attempt (even by a different valid user)
    res2 = redeem_discount_code("SUMMER20", "user_002", mock_context)

    assert res2["status"] == "error"
    assert "already been redeemed" in res2["error"]
    # The original state should be preserved
    assert DISCOUNT_CODES["SUMMER20"]["redeemed_by"] == "user_001"
