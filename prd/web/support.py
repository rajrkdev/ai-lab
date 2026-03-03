"""Support Chatbot — Developer support chat UI (Port 8502).

This is the frontend for API developers and integration partners.  It provides:
  - A chat interface for asking about API errors, payload structure, integration
  - Multi-turn conversation history within each session (server-side)
  - Confidence scores, source citations, and LLM model labels per answer
  - Thumbs-up / thumbs-down feedback buttons on each response
  - Session management with auto-generated session IDs

All backend calls go to the FastAPI server at http://localhost:8000.
Conversation history is maintained server-side per session_id.
This app runs on port 8502 (started by run.ps1).
"""

import streamlit as st

from web.chatbot_ui import run_chatbot

# Page configuration — sets the browser tab title and icon
st.set_page_config(
    page_title="InsureChat — API Support",
    page_icon="\U0001f527",
    layout="wide",
)

SUPPORT_CONFIG = {
    "chatbot_type": "support",
    "chat_endpoint": "/chat/support",
    "sidebar_title": "\U0001f527 InsureChat Support",
    "sidebar_caption": "API Developer Support — v3.0",
    "upload_subheader": "\U0001f4c4 Upload API Docs",
    "upload_label": "Upload API error/support documents",
    "upload_types": ["md", "txt", "json", "yaml", "yml"],
    "upload_help": "Upload API error docs, payload specs, or integration guides",
    "main_title": "\U0001f527 InsureChat — API Developer Support",
    "main_caption": "Paste error messages, describe API issues, or ask about integration details.",
    "chat_placeholder": "Describe your API error or integration issue...",
    "spinner_text": "Searching API documentation...",
}


def main():
    """Main entry point — renders the full support chatbot UI."""
    run_chatbot(SUPPORT_CONFIG)


if __name__ == "__main__":
    main()
