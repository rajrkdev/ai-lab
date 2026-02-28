"""Intent classification — Claude Haiku classification of user queries.

Before the RAG pipeline retrieves documents, this module classifies the user's
query into a specific intent category using a lightweight Claude Haiku call.
The classified intent is stored in analytics and helps track which topics users
ask about most frequently.

Intents are split by chatbot type:
  - microsite: policy_coverage, claims_process, premium_billing, etc.
  - support:   authentication_error, validation_error, endpoint_usage, etc.

If classification fails (API error, missing key), it gracefully returns 'other'.
"""

import os
from typing import Optional

import anthropic
from dotenv import load_dotenv

from mcp_server.tools.config_manager import get_llm_config

load_dotenv()

# ---------------------------------------------------------------------------
# Classification prompt template — sent to Claude Haiku with the user's query.
# The model is instructed to return ONLY the category name (one word/phrase).
# ---------------------------------------------------------------------------
INTENT_PROMPT = """Classify the following customer query into exactly ONE category.
Respond with ONLY the category name, nothing else.

MICROSITE CATEGORIES:
- policy_coverage
- claims_process
- premium_billing
- policy_renewal
- cancellation
- new_policy
- emergency_contact
- general_faq
- other

SUPPORT CATEGORIES:
- authentication_error
- validation_error
- rate_limit_error
- payload_structure
- endpoint_usage
- integration_setup
- api_key_issue
- other

Query: {user_query}
Chatbot type: {chatbot_type}
Category:"""

# Whitelist of valid intent names per chatbot type.
# If the LLM returns something outside this list, we fall back to 'other'.
VALID_INTENTS = {
    "microsite": [
        "policy_coverage", "claims_process", "premium_billing",
        "policy_renewal", "cancellation", "new_policy",
        "emergency_contact", "general_faq", "other",
    ],
    "support": [
        "authentication_error", "validation_error", "rate_limit_error",
        "payload_structure", "endpoint_usage", "integration_setup",
        "api_key_issue", "other",
    ],
}


def classify_intent(query: str, chatbot_type: str = "microsite") -> str:
    """Classify user query intent using Claude Haiku.

    Makes a single LLM call with temperature=0 for deterministic output.
    Validates the response against the known intent list and returns 'other'
    if the model hallucinates an unknown category or the API fails.

    Returns:
        Intent category string (e.g. 'policy_coverage'), or 'other' on failure.
    """
    # Read which classifier model to use from config.yaml
    llm_cfg = get_llm_config()
    classifier_model = llm_cfg.get("classifier", "claude-haiku-4-5-20251001")

    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "other"

        client = anthropic.Anthropic(api_key=api_key)
        prompt = INTENT_PROMPT.format(user_query=query, chatbot_type=chatbot_type)

        message = client.messages.create(
            model=classifier_model,
            max_tokens=50,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )

        intent = message.content[0].text.strip().lower()

        # Validate against known intents
        valid = VALID_INTENTS.get(chatbot_type, VALID_INTENTS["microsite"])
        if intent in valid:
            return intent
        return "other"

    except Exception:
        return "other"
