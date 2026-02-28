"""Intent classification — Async Claude Haiku classification of user queries."""

import os
from typing import Optional

import anthropic
from dotenv import load_dotenv

from mcp_server.tools.config_manager import get_llm_config

load_dotenv()

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

    Returns intent category string, or 'other' on failure.
    """
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
