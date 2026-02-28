# InsureChat v3.0 — Web Package
# This package contains the web-facing components of the application:
#   - fastapi_server.py     — REST API backend (all /chat, /ingest, /analytics, /reports endpoints)
#   - streamlit_microsite.py — Insurance customer chatbot UI (port 8501)
#   - streamlit_support.py   — API developer support chatbot UI (port 8502)
#
# The Streamlit apps communicate with the FastAPI backend via HTTP requests
# (localhost:8000).  All three services are started together by run.ps1.
