"""Microsite Chatbot — Insurance customer chat UI (Port 8501).

This is the frontend for insurance customers.  It provides:
  - A chat interface where users ask policy, claims, billing questions
  - Multi-turn conversation history within each session (server-side)
  - Confidence scores, source citations, and LLM model labels per answer
  - Thumbs-up / thumbs-down feedback buttons on each response
  - Session management (new session button, auto-generated session IDs)

All backend calls go to the FastAPI server at http://localhost:8000.
Conversation history is maintained server-side per session_id.
This app runs on port 8501 (started by run.ps1).
"""

import streamlit as st

from web.chatbot_ui import run_chatbot

# Page configuration — sets the browser tab title and icon
st.set_page_config(
    page_title="InsureChat — Insurance Assistant",
    page_icon="\U0001f3e0",
    layout="wide",
)

MICROSITE_CONFIG = {
    "chatbot_type": "microsite",
    "chat_endpoint": "/chat/microsite",
    "sidebar_title": "\U0001f3e0 InsureChat",
    "sidebar_caption": "Insurance Assistant — v3.0",
    "upload_subheader": "\U0001f4c4 Upload Documents",
    "upload_label": "Upload insurance documents",
    "upload_types": ["pdf", "docx", "txt", "md"],
    "upload_help": "Upload policy documents, FAQs, or coverage guides",
    "main_title": "\U0001f3e0 InsureChat — Insurance Assistant",
    "main_caption": "Ask questions about your insurance policies, coverage, claims, and more.",
    "chat_placeholder": "Ask about your insurance policy...",
    "spinner_text": "Searching knowledge base...",
}


def main():
    """Main entry point — renders the full microsite chatbot UI."""
    run_chatbot(MICROSITE_CONFIG)


if __name__ == "__main__":
    main()
