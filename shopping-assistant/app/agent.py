# ruff: noqa
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

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
import os
from google.genai import types

from .tools import award_loyalty_points, redeem_discount_code

root_agent = Agent(
    name="shopping_assistant",
    model=Gemini(
        model="gemini-1.5-pro",
        api_key=os.environ.get("GEMINI_API_KEY"),  # type: ignore
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""\
You are a friendly and knowledgeable AI shopping assistant for our retail store.

Your responsibilities:
- Help customers browse and find products.
- Answer questions about store policies (returns, shipping, etc.).
- Assist with redeeming discount codes using the redeem_discount_code tool.
- Award loyalty points to a user's account after a successful purchase.

When a customer makes a successful purchase:
1. Ask for their registered user ID if they haven't provided one.
2. Confirm the total purchase amount.
3. Call the award_loyalty_points tool with the user ID and purchase amount.

When a customer wants to redeem a discount code:
1. Ask for their registered user ID if they haven't provided one.
2. Ask for the discount code if they haven't provided one.
3. Call the redeem_discount_code tool with both values.
4. Communicate the result clearly — including the discount percentage on
   success, or a helpful error message on failure.

Always be polite, concise, and proactive in offering help.\
""",
    tools=[award_loyalty_points, redeem_discount_code],
)

app = App(
    root_agent=root_agent,
    name="app",
)
