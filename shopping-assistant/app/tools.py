# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Custom tools for the shopping assistant agent."""

from google.adk.tools import ToolContext
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# In-memory discount-code store
# ---------------------------------------------------------------------------
# Each code maps to its metadata. ``redeemed_by`` starts as ``None`` and is
# set to the user ID that redeems it - ensuring single-use semantics.
# ---------------------------------------------------------------------------
DISCOUNT_CODES: dict[str, dict] = {
    "WELCOME50": {
        "discount_percent": 50,
        "description": "50% off your first purchase",
        "redeemed_by": None,
    },
    "SUMMER20": {
        "discount_percent": 20,
        "description": "20% summer sale discount",
        "redeemed_by": None,
    },
}

# Simple set of "registered" user IDs for demo purposes.
REGISTERED_USERS: set[str] = {"user_001", "user_002", "user_003"}

# In-memory store for user loyalty points
USER_LOYALTY_POINTS: dict[str, int] = {
    "user_001": 0,
    "user_002": 0,
    "user_003": 0,
}


def redeem_discount_code(
    discount_code: str,
    user_id: str,
    tool_context: ToolContext,
) -> dict:
    """Redeem a single-use discount code for a registered user.

    Validates that the user is registered, the code exists, and it has not
    already been redeemed. On success the code is marked as used so it cannot
    be redeemed again.

    Args:
        discount_code: The discount code string to redeem (e.g. WELCOME50).
        user_id: The registered user ID attempting to redeem the code.

    Returns:
        A dict with the redemption result including status, discount details,
        or an error message.
    """
    # --- Guard: registered user required ---
    if user_id not in REGISTERED_USERS:
        return {
            "status": "error",
            "error": f"User '{user_id}' is not a registered user. "
            "Please register before redeeming discount codes.",
        }

    code_upper = discount_code.strip().upper()

    # --- Guard: code must exist ---
    if code_upper not in DISCOUNT_CODES:
        return {
            "status": "error",
            "error": f"Discount code '{code_upper}' not found.",
        }

    code_entry = DISCOUNT_CODES[code_upper]

    # --- Guard: single-use check ---
    if code_entry["redeemed_by"] is not None:
        return {
            "status": "error",
            "error": f"Discount code '{code_upper}' has already been redeemed.",
        }

    # --- Redeem the code ---
    code_entry["redeemed_by"] = user_id

    # Persist the active discount in session state so the agent can
    # reference it in follow-up turns.
    tool_context.state["active_discount"] = {
        "code": code_upper,
        "discount_percent": code_entry["discount_percent"],
        "user_id": user_id,
    }

    return {
        "status": "success",
        "message": f"Code '{code_upper}' redeemed successfully!",
        "discount_percent": code_entry["discount_percent"],
        "description": code_entry["description"],
        "user_id": user_id,
    }


class AwardPointsInput(BaseModel):
    user_id: str = Field(..., description="The registered user ID.")
    purchase_amount: float = Field(
        ..., description="The total purchase amount in dollars."
    )

    @field_validator("purchase_amount")
    @classmethod
    def check_amount_positive_and_capped(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Purchase amount must be greater than zero.")
        if v > 10000:
            raise ValueError("Purchase amount exceeds maximum allowed per transaction.")
        return v


def award_loyalty_points(
    user_id: str,
    purchase_amount: float,
    tool_context: ToolContext,
) -> dict:
    """Award loyalty points to a registered user after a purchase.

    Validates the input using strict Pydantic schemas, calculates points
    (1 point per $1 spent), and updates the user's loyalty points balance.

    Args:
        user_id: The registered user ID.
        purchase_amount: The total purchase amount in dollars.

    Returns:
        A dict with the result of the point allocation.
    """
    try:
        # Strict input validation via Pydantic
        validated_input = AwardPointsInput(
            user_id=user_id, purchase_amount=purchase_amount
        )
    except Exception as e:
        return {
            "status": "error",
            "error": f"Input validation failed: {e!s}",
        }

    # Guard: registered user required
    if validated_input.user_id not in REGISTERED_USERS:
        return {
            "status": "error",
            "error": f"User '{validated_input.user_id}' is not a registered user.",
        }

    # Guard: user must have a loyalty points account
    if validated_input.user_id not in USER_LOYALTY_POINTS:
        return {
            "status": "error",
            "error": f"User '{validated_input.user_id}' does not have a loyalty points account.",
        }

    # Calculate points (1 point per $1 spent, rounded down)
    points_to_award = int(validated_input.purchase_amount)

    # Award points
    USER_LOYALTY_POINTS[validated_input.user_id] += points_to_award

    return {
        "status": "success",
        "message": f"Successfully awarded {points_to_award} loyalty points.",
        "new_balance": USER_LOYALTY_POINTS[validated_input.user_id],
        "user_id": validated_input.user_id,
    }
