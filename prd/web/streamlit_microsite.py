"""Streamlit Microsite Chatbot — Insurance customer chat UI (Port 8501)."""

import uuid

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="InsureChat — Insurance Assistant",
    page_icon="🏠",
    layout="wide",
)


def init_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"sess_{uuid.uuid4().hex[:8]}"
    if "messages" not in st.session_state:
        st.session_state.messages = []


def send_chat(query: str) -> dict:
    """Send chat query to FastAPI backend."""
    try:
        resp = requests.post(
            f"{API_BASE}/chat/microsite",
            json={"query": query, "session_id": st.session_state.session_id},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"response": "Cannot connect to the backend server. Make sure FastAPI is running on port 8000.", "blocked": True, "sources": [], "confidence_score": 0}
    except Exception as e:
        return {"response": f"Error: {str(e)}", "blocked": True, "sources": [], "confidence_score": 0}


def upload_document(file) -> dict:
    """Upload document to backend for ingestion."""
    try:
        resp = requests.post(
            f"{API_BASE}/ingest",
            files={"file": (file.name, file.getvalue(), file.type or "application/octet-stream")},
            data={"chatbot_type": "microsite", "category": "general"},
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"status": "error", "error": "Cannot connect to backend server."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    init_session()

    # Sidebar
    with st.sidebar:
        st.title("🏠 InsureChat")
        st.caption("Insurance Assistant — v3.0")
        st.divider()

        # Document upload
        st.subheader("📄 Upload Documents")
        uploaded_file = st.file_uploader(
            "Upload insurance documents",
            type=["pdf", "docx", "txt", "md"],
            help="Upload policy documents, FAQs, or coverage guides",
        )
        if uploaded_file and st.button("📤 Ingest Document"):
            with st.spinner("Ingesting document..."):
                result = upload_document(uploaded_file)
            if result.get("status") == "success":
                st.success(f"✅ {result['chunks_ingested']} chunks ingested from {result['source']}")
            else:
                st.error(f"❌ Ingestion failed: {result.get('error', result.get('status'))}")

        st.divider()

        # Session info
        st.caption(f"Session: {st.session_state.session_id}")
        if st.button("🔄 New Session"):
            st.session_state.session_id = f"sess_{uuid.uuid4().hex[:8]}"
            st.session_state.messages = []
            st.rerun()

        st.divider()

        # Analytics link
        st.subheader("📊 Analytics")
        st.markdown("[Open Analytics Dashboard](http://localhost:8000/analytics)")

    # Main chat area
    st.title("🏠 InsureChat — Insurance Assistant")
    st.caption("Ask questions about your insurance policies, coverage, claims, and more.")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("metadata"):
                meta = msg["metadata"]
                cols = st.columns(4)
                if meta.get("confidence_score"):
                    confidence = meta["confidence_score"]
                    color = "green" if confidence >= 0.75 else ("orange" if confidence >= 0.60 else "red")
                    cols[0].markdown(f"**Confidence:** :{color}[{confidence:.0%}]")
                if meta.get("sources"):
                    cols[1].markdown(f"**Sources:** {', '.join(meta['sources'][:3])}")
                if meta.get("llm_used") and meta["llm_used"] != "none":
                    cols[2].markdown(f"**LLM:** {meta['llm_used']}")
                if meta.get("response_time_ms"):
                    cols[3].markdown(f"**Time:** {meta['response_time_ms']}ms")
                if meta.get("blocked"):
                    st.warning(f"🚫 BLOCKED — Reason: {meta.get('reason', 'security')}")

    # Chat input
    if prompt := st.chat_input("Ask about your insurance policy..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                result = send_chat(prompt)

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

            # Display metadata
            cols = st.columns(4)
            if metadata["confidence_score"]:
                confidence = metadata["confidence_score"]
                color = "green" if confidence >= 0.75 else ("orange" if confidence >= 0.60 else "red")
                cols[0].markdown(f"**Confidence:** :{color}[{confidence:.0%}]")
            if metadata["sources"]:
                cols[1].markdown(f"**Sources:** {', '.join(metadata['sources'][:3])}")
            if metadata["llm_used"] != "none":
                cols[2].markdown(f"**LLM:** {metadata['llm_used']}")
            if metadata["response_time_ms"]:
                cols[3].markdown(f"**Time:** {metadata['response_time_ms']}ms")
            if metadata["blocked"]:
                st.warning(f"🚫 BLOCKED — Reason: {metadata.get('reason', 'security')}")

            # Feedback buttons
            if metadata.get("message_id"):
                col1, col2, _ = st.columns([1, 1, 8])
                with col1:
                    if st.button("👍", key=f"up_{metadata['message_id']}"):
                        requests.post(f"{API_BASE}/feedback", json={"message_id": metadata["message_id"], "rating": 1}, timeout=5)
                        st.toast("Thanks for the feedback!")
                with col2:
                    if st.button("👎", key=f"down_{metadata['message_id']}"):
                        requests.post(f"{API_BASE}/feedback", json={"message_id": metadata["message_id"], "rating": -1}, timeout=5)
                        st.toast("Thanks for the feedback!")

            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "metadata": metadata,
            })


if __name__ == "__main__":
    main()
