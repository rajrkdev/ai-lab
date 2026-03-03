# InsureChat v3.0 — Web Package
# This package contains the web-facing components of the application:
#   - fastapi_server.py — REST API backend (all /chat, /ingest, /analytics, /reports endpoints)
#   - admin.py          — Admin dashboard UI for ingestion & management (port 8500)
#   - microsite.py      — Insurance customer chatbot UI (port 8501)
#   - support.py        — API developer support chatbot UI (port 8502)
#   - chatbot_ui.py     — Shared chatbot UI components
#
# The Streamlit apps communicate with the FastAPI backend via HTTP requests
# (localhost:8000).  All four services are started together by run.ps1.
