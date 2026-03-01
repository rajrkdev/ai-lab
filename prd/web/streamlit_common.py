"""Shared Streamlit chatbot UI components.

Contains the common logic used by both streamlit_microsite.py (Port 8501) and
streamlit_support.py (Port 8502).  Each chatbot entry point configures the
UI via a config dict and delegates rendering to run_chatbot().
"""

import uuid

import requests
import streamlit as st

# Base URL of the FastAPI backend (must be running before this app starts)
API_BASE = "http://localhost:8000"


def init_session():
    """Initialize Streamlit session state with a unique session ID and empty chat history."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"sess_{uuid.uuid4().hex[:8]}"
    if "messages" not in st.session_state:
        st.session_state.messages = []


def send_chat(query, endpoint):
    """Send the user's query to the specified FastAPI chat endpoint.

    Returns the JSON response dict with: response, sources, confidence_score,
    llm_used, response_time_ms, blocked, reason, message_id.
    """
    try:
        resp = requests.post(
            f"{API_BASE}{endpoint}",
            json={"query": query, "session_id": st.session_state.session_id},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {
            "response": "Cannot connect to the backend server. "
                        "Make sure FastAPI is running on port 8000.",
            "blocked": True,
            "sources": [],
            "confidence_score": 0,
        }
    except Exception as e:
        return {
            "response": f"Error: {str(e)}",
            "blocked": True,
            "sources": [],
            "confidence_score": 0,
        }


def upload_document(file, chatbot_type):
    """Upload a document to the FastAPI /ingest endpoint for ingestion.

    Sends the file as multipart form data with the given chatbot_type.
    Returns the ingestion result: chunks_ingested, status, source.
    """
    try:
        resp = requests.post(
            f"{API_BASE}/ingest",
            files={"file": (file.name, file.getvalue(),
                            file.type or "application/octet-stream")},
            data={"chatbot_type": chatbot_type, "category": "general"},
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"status": "error", "error": "Cannot connect to backend server."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _render_metadata(meta):
    """Render confidence, sources, LLM, and response time in 4 columns."""
    cols = st.columns(4)
    if meta.get("confidence_score"):
        confidence = meta["confidence_score"]
        color = ("green" if confidence >= 0.75
                 else ("orange" if confidence >= 0.60 else "red"))
        cols[0].markdown(f"**Confidence:** :{color}[{confidence:.0%}]")
    if meta.get("sources"):
        cols[1].markdown(
            f"**Sources:** {', '.join(meta['sources'][:3])}")
    if meta.get("llm_used") and meta["llm_used"] != "none":
        cols[2].markdown(f"**LLM:** {meta['llm_used']}")
    if meta.get("response_time_ms"):
        cols[3].markdown(f"**Time:** {meta['response_time_ms']}ms")
    if meta.get("blocked"):
        st.warning(
            f"\U0001f6ab BLOCKED \u2014 Reason: {meta.get('reason', 'security')}")


def _render_feedback_buttons(metadata):
    """Render thumbs-up / thumbs-down feedback buttons."""
    if not metadata.get("message_id"):
        return
    col1, col2, _ = st.columns([1, 1, 8])
    msg_id = metadata["message_id"]
    with col1:
        if st.button("\U0001f44d", key=f"up_{msg_id}"):
            requests.post(
                f"{API_BASE}/feedback",
                json={"message_id": msg_id, "rating": 1},
                timeout=5,
            )
            st.toast("Thanks for the feedback!")
    with col2:
        if st.button("\U0001f44e", key=f"down_{msg_id}"):
            requests.post(
                f"{API_BASE}/feedback",
                json={"message_id": msg_id, "rating": -1},
                timeout=5,
            )
            st.toast("Thanks for the feedback!")


def _render_chat_history():
    """Render all previous messages in the session."""
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("metadata"):
                _render_metadata(msg["metadata"])


def _handle_chat_input(config):
    """Handle new user input: send to API, display response, save to session."""
    prompt = st.chat_input(config["chat_placeholder"])
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(config["spinner_text"]):
            result = send_chat(prompt, config["chat_endpoint"])

        st.markdown(result["response"])

        metadata = {
            "confidence_score": result.get("confidence_score", 0),
            "sources": result.get("sources", []),
            "llm_used": result.get("llm_used", "none"),
            "response_time_ms": result.get("response_time_ms", 0),
            "blocked": result.get("blocked", False),
            "reason": result.get("reason"),
            "message_id": result.get("message_id"),
        }

        _render_metadata(metadata)
        _render_feedback_buttons(metadata)

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["response"],
            "metadata": metadata,
        })


def _render_sidebar(config):
    """Render the sidebar with branding, upload, session controls, analytics link."""
    with st.sidebar:
        st.title(config["sidebar_title"])
        st.caption(config["sidebar_caption"])
        st.divider()

        # Document upload
        st.subheader(config["upload_subheader"])
        uploaded_file = st.file_uploader(
            config["upload_label"],
            type=config["upload_types"],
            help=config["upload_help"],
        )
        if uploaded_file and st.button("\U0001f4e4 Ingest Document"):
            with st.spinner("Ingesting document..."):
                result = upload_document(uploaded_file, config["chatbot_type"])
            if result.get("status") == "success":
                st.success(
                    f"\u2705 {result['chunks_ingested']} chunks ingested "
                    f"from {result['source']}")
            else:
                st.error(
                    f"\u274c Ingestion failed: "
                    f"{result.get('error', result.get('status'))}")

        st.divider()

        # Session info
        st.caption(f"Session: {st.session_state.session_id}")
        if st.button("\U0001f504 New Session"):
            st.session_state.session_id = f"sess_{uuid.uuid4().hex[:8]}"
            st.session_state.messages = []
            st.rerun()

        st.divider()

        # Analytics link
        st.subheader("\U0001f4ca Analytics")
        st.markdown(
            "[Open Analytics Dashboard](http://localhost:8000/analytics)")


def run_chatbot(config):
    """Run a full chatbot UI with the given configuration.

    Args:
        config: dict with keys:
            chatbot_type, chat_endpoint, sidebar_title, sidebar_caption,
            upload_subheader, upload_label, upload_types, upload_help,
            main_title, main_caption, chat_placeholder, spinner_text.
    """
    init_session()
    _render_sidebar(config)

    st.title(config["main_title"])
    st.caption(config["main_caption"])

    _render_chat_history()
    _handle_chat_input(config)
