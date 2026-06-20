# STRIDE Threat Model Assessment: Shopping Assistant

## 1. System Boundaries

### Entry Points
- **User Interface / API**: FastAPI endpoints handling conversational inputs from users.
- **LLM Reasoning**: The Gemini 1.5 Pro model interpreting user intent and invoking tools.
- **Tool Execution**: The `redeem_discount_code` function invoked by the LLM.

### Data Storage & State
- **Session State**: In-memory dictionary storing the `active_discount` for the current conversation.
- **Application State**: In-memory dictionaries and sets (`DISCOUNT_CODES`, `REGISTERED_USERS`) functioning as a mock database.

### External Dependencies
- **Google Gemini API**: External LLM provider, accessed via network calls using an API key stored in the environment.

---

## 2. STRIDE Evaluation

### S - Spoofing (Identity)
**Vulnerability**: Identity Verification Bypass
- **Description**: The `redeem_discount_code` tool relies on the LLM to provide the `user_id` parameter. The LLM extracts this from the user's conversational input. There is no cryptographic or session-based authentication verifying that the person interacting with the agent is actually the owner of that `user_id`.
- **Impact**: Any user can spoof their identity by simply typing "I am user_001" and successfully redeem a code on behalf of someone else.

### T - Tampering (Data)
**Vulnerability**: Volatile and Unprotected State
- **Description**: The `DISCOUNT_CODES` database is an in-memory Python dictionary. While the tool correctly marks `redeemed_by`, this data is lost upon application restart.
- **Vulnerability**: Prompt Injection
- **Description**: While the tool controls state mutation, an attacker might use prompt injection to confuse the LLM into passing incorrect arguments (e.g., passing a different user's ID while redeeming a code).

### R - Repudiation (Logging)
**Vulnerability**: Lack of Audit Logging
- **Description**: The system currently lacks an audit trail. When `redeem_discount_code` is executed, the only change is a mutation of an in-memory dictionary.
- **Impact**: If a dispute arises over whether a code was used, or if malicious activity occurs, there are no logs to investigate. All evidence disappears if the FastAPI server restarts.

### I - Information Disclosure (Data Leakage)
**Vulnerability**: Enumeration via Error Messages
- **Description**: The tool returns highly specific error messages, such as `"User '{user_id}' is not a registered user."` or `"Discount code '{code_upper}' not found."`
- **Impact**: An attacker can systematically guess user IDs or discount codes based on the error responses relayed back by the LLM, mapping out valid users and promotions.

### D - Denial of Service (Resource Exhaustion)
**Vulnerability**: Unbounded LLM API Invocations
- **Description**: There are no apparent rate limits on the FastAPI endpoints.
- **Impact**: An attacker could flood the agent with complex requests, rapidly exhausting the Google Gemini API quota, inflating billing costs, or causing memory exhaustion on the local server due to unbounded session state growth.

### E - Elevation of Privilege (Access Control)
**Vulnerability**: Missing Authorization Layer
- **Description**: Because authentication is absent (Spoofing), authorization is inherently broken. The agent assumes that if a user provides a registered ID, they are authorized to perform actions for that ID.
- **Impact**: Unauthenticated users have the same privileges as authenticated users within the context of the chat session, allowing them to execute privileged tool actions like discount redemption.

---

## 3. Recommended Mitigations

1. **Implement Real Authentication**: Do not trust the LLM to verify user identity via text prompts. Integrate OAuth or JWT-based authentication at the FastAPI layer, and pass the verified `user_id` securely via the `ToolContext` rather than as an LLM-provided argument.
2. **Persistent Storage**: Move `DISCOUNT_CODES` and `REGISTERED_USERS` to a persistent database (e.g., Cloud SQL or Firestore) to prevent state loss and tampering across restarts.
3. **Audit Logging**: Implement structured logging within the `redeem_discount_code` tool to record timestamps, user IDs, and discount codes for every redemption attempt.
4. **Generic Error Messages**: Refactor tool error messages to be less descriptive to prevent enumeration attacks (e.g., "Invalid redemption attempt").
5. **Rate Limiting**: Apply rate limiting middleware to the FastAPI application to mitigate DoS risks.
