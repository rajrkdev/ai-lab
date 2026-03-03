"""InsureChat Admin — Document Ingestion, Analytics & Collection Management.

Single Streamlit app (port 8500) with three tabs:
  1. Document Ingestion  — Upload files into any chatbot collection (bulk)
  2. Analytics Dashboard — KPIs, charts, sessions, anomalies, report downloads
  3. Collections         — Browse, preview, delete documents & purge collections

All operations go through the FastAPI backend REST API.

To add a new chatbot type: add an entry to CHATBOT_REGISTRY below.
All three tabs auto-populate from the registry — no other code changes needed.
"""

import requests
import streamlit as st

st.set_page_config(
    page_title="InsureChat Admin",
    page_icon="⚙️",
    layout="wide",
)

# Base URL of the FastAPI backend
API_BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Chatbot Registry — add new chatbot types here
# ---------------------------------------------------------------------------
CHATBOT_REGISTRY = {
    "microsite": {
        "label": "🏠 Insurance Microsite",
        "collection": "insurance_docs",
        "allowed_extensions": ["pdf", "docx", "txt", "md"],
        "description": "Insurance policies, FAQs, coverage guides",
    },
    "support": {
        "label": "🔧 API Support",
        "collection": "support_docs",
        "allowed_extensions": ["md", "txt", "json", "yaml", "yml"],
        "description": "API documentation, error specs, integration guides",
    },
}


# ---------------------------------------------------------------------------
# Helper: chatbot selector widget (reused across tabs)
# ---------------------------------------------------------------------------
def _chatbot_selector(key: str):
    """Render a selectbox for choosing a chatbot type. Returns (chatbot_key, config)."""
    options = list(CHATBOT_REGISTRY.keys())
    labels = [CHATBOT_REGISTRY[k]["label"] for k in options]
    idx = st.selectbox("Chatbot", labels, key=key)
    selected_key = options[labels.index(idx)]
    return selected_key, CHATBOT_REGISTRY[selected_key]


# ---------------------------------------------------------------------------
# Tab 1: Document Ingestion
# ---------------------------------------------------------------------------
def _render_ingestion_tab():
    st.header("📤 Document Ingestion")
    st.caption("Upload documents into any chatbot's knowledge base. Supports bulk upload.")

    chatbot_key, config = _chatbot_selector("ingest_chatbot")
    st.info(f"**Target collection:** `{config['collection']}` — {config['description']}")

    category = st.text_input("Category", value="general", help="Tag for organising documents (e.g. 'policy', 'faq', 'api-v2').")

    uploaded_files = st.file_uploader(
        "Choose files",
        type=config["allowed_extensions"],
        accept_multiple_files=True,
        help=f"Allowed types: {', '.join(config['allowed_extensions'])}",
    )

    if uploaded_files and st.button("🚀 Ingest All", type="primary"):
        progress = st.progress(0, text="Starting ingestion...")
        results = []

        for i, file in enumerate(uploaded_files):
            progress.progress(
                (i) / len(uploaded_files),
                text=f"Ingesting {file.name}...",
            )
            try:
                resp = requests.post(
                    f"{API_BASE}/ingest",
                    files={"file": (file.name, file.getvalue(),
                                    file.type or "application/octet-stream")},
                    data={"chatbot_type": chatbot_key, "category": category},
                    timeout=300,
                )
                resp.raise_for_status()
                data = resp.json()
                results.append({
                    "File": file.name,
                    "Chunks": data.get("chunks_ingested", 0),
                    "Status": data.get("status", "unknown"),
                })
            except requests.exceptions.ConnectionError:
                results.append({"File": file.name, "Chunks": 0, "Status": "error: backend unreachable"})
            except Exception as e:
                results.append({"File": file.name, "Chunks": 0, "Status": f"error: {e}"})

        progress.progress(1.0, text="Done!")

        # Summary table
        st.subheader("Results")
        import pandas as pd
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)

        success_count = sum(1 for r in results if r["Status"] == "success")
        total = len(results)
        if success_count == total:
            st.success(f"✅ All {total} files ingested successfully.")
        else:
            st.warning(f"⚠️ {success_count}/{total} files ingested successfully.")


# ---------------------------------------------------------------------------
# Tab 2: Analytics Dashboard
# ---------------------------------------------------------------------------
def _render_analytics_tab():
    from analytics.dashboard import render_dashboard
    render_dashboard()


# ---------------------------------------------------------------------------
# Tab 3: Collection Browser
# ---------------------------------------------------------------------------
def _fetch_collection_stats():
    """Fetch stats for all collections from the management API."""
    try:
        resp = requests.get(f"{API_BASE}/management/collections", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def _fetch_documents(collection_name):
    """Fetch list of documents in a collection."""
    try:
        resp = requests.get(
            f"{API_BASE}/management/collections/{collection_name}/documents",
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def _fetch_chunks(collection_name, source_name):
    """Fetch all chunks for a specific document."""
    try:
        resp = requests.get(
            f"{API_BASE}/management/collections/{collection_name}/documents/{requests.utils.quote(source_name, safe='')}/chunks",
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def _delete_document(collection_name, source_name):
    """Delete a document from a collection."""
    try:
        resp = requests.delete(
            f"{API_BASE}/management/collections/{collection_name}/documents/{requests.utils.quote(source_name, safe='')}",
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _purge_collection(collection_name):
    """Purge an entire collection."""
    try:
        resp = requests.delete(
            f"{API_BASE}/management/collections/{collection_name}",
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _render_collections_tab():
    st.header("📁 Collection Browser")
    st.caption("Browse, preview, and manage documents in each chatbot's knowledge base.")

    chatbot_key, config = _chatbot_selector("coll_chatbot")
    collection_name = config["collection"]

    # --- Stats panel ---
    all_stats = _fetch_collection_stats()
    stats = next((s for s in all_stats if s["collection_name"] == collection_name), None)

    if stats:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Chunks", stats["total_chunks"])
        col2.metric("Unique Documents", stats["unique_documents"])
        col3.metric("Avg Chunks / Doc", stats["avg_chunks_per_doc"])
    else:
        st.info("No stats available. The backend may not be running.")

    st.divider()

    # --- Documents table ---
    documents = _fetch_documents(collection_name)

    if not documents:
        st.info("No documents in this collection yet. Use the Ingestion tab to upload.")
        return

    st.subheader(f"Documents in `{collection_name}`")

    for doc in documents:
        source = doc["source"]
        category = doc.get("category", "general")
        chunk_count = doc.get("chunk_count", 0)

        with st.expander(f"📄 {source}  —  {chunk_count} chunks  |  category: {category}"):
            # Preview chunks
            chunks = _fetch_chunks(collection_name, source)
            if chunks:
                for chunk in chunks:
                    idx = chunk.get("chunk_index", "?")
                    total = chunk.get("total_chunks", "?")
                    st.markdown(f"**Chunk {idx}/{total}**")
                    st.code(chunk.get("text", ""), language=None)
            else:
                st.warning("Could not load chunks.")

            # Delete button
            if st.button(f"🗑️ Delete '{source}'", key=f"del_{collection_name}_{source}"):
                result = _delete_document(collection_name, source)
                if result.get("status") == "deleted":
                    st.success(f"Deleted {result.get('chunks_deleted', 0)} chunks from '{source}'.")
                    st.rerun()
                else:
                    st.error(f"Delete failed: {result.get('error', result.get('status'))}")

    # --- Purge collection ---
    st.divider()
    st.subheader("⚠️ Danger Zone")
    st.warning(f"Purging will permanently delete **all** documents in `{collection_name}`.")

    confirm_text = st.text_input(
        f"Type `{collection_name}` to confirm purge:",
        key=f"purge_confirm_{collection_name}",
    )
    if st.button("🔥 Purge Collection", type="secondary", key=f"purge_{collection_name}"):
        if confirm_text == collection_name:
            result = _purge_collection(collection_name)
            if result.get("status") == "purged":
                st.success(f"Collection `{collection_name}` purged.")
                st.rerun()
            else:
                st.error(f"Purge failed: {result.get('error', result.get('status'))}")
        else:
            st.error(f"Confirmation text doesn't match. Please type `{collection_name}` exactly.")


# ---------------------------------------------------------------------------
# Main Layout
# ---------------------------------------------------------------------------
st.title("⚙️ InsureChat Admin")

tab_ingest, tab_analytics, tab_collections = st.tabs([
    "📤 Document Ingestion",
    "📊 Analytics",
    "📁 Collections",
])

with tab_ingest:
    _render_ingestion_tab()

with tab_analytics:
    _render_analytics_tab()

with tab_collections:
    _render_collections_tab()
