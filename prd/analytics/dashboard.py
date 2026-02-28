"""Analytics Dashboard — Streamlit component with 5 KPI cards and 4 charts."""

import requests
import streamlit as st

API_BASE = "http://localhost:8000"


def fetch_analytics(chatbot_type: str = None, days: int = 30) -> dict:
    """Fetch analytics data from FastAPI."""
    try:
        params = {"days": days}
        if chatbot_type:
            params["chatbot_type"] = chatbot_type
        resp = requests.get(f"{API_BASE}/analytics", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def fetch_sessions(chatbot_type: str = None, limit: int = 20) -> list:
    """Fetch recent sessions."""
    try:
        params = {"limit": limit}
        if chatbot_type:
            params["chatbot_type"] = chatbot_type
        resp = requests.get(f"{API_BASE}/analytics/sessions", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def fetch_anomalies() -> dict:
    """Fetch anomaly detection results."""
    try:
        resp = requests.get(f"{API_BASE}/analytics/anomalies", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def render_dashboard():
    """Render the full analytics dashboard as a Streamlit component."""
    st.header("📊 Analytics Dashboard")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        chatbot_filter = st.selectbox("Chatbot Type", ["All", "microsite", "support"])
    with col2:
        days_filter = st.selectbox("Time Range", [7, 14, 30, 90], index=2)

    cb_type = None if chatbot_filter == "All" else chatbot_filter
    data = fetch_analytics(cb_type, days_filter)

    if "error" in data:
        st.error(f"Cannot fetch analytics: {data['error']}")
        return

    summary = data.get("summary", {})
    time_series = data.get("time_series", [])
    intents = data.get("intent_distribution", [])

    # --- KPI Cards (5) ---
    st.subheader("Key Performance Indicators")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    kpi1.metric("Total Chats", summary.get("total_sessions", 0))
    success_rate = summary.get("success_rate", 0)
    kpi2.metric("Success Rate", f"{success_rate:.1f}%")
    kpi3.metric("Avg Response Time", f"{summary.get('avg_response_time_ms', 0):.0f}ms")
    kpi4.metric("CSAT Score", f"{summary.get('csat', 3.0):.1f}/5.0")
    kpi5.metric("Security Events", summary.get("security_events", 0))

    st.divider()

    # --- Chart 1: Response Time Trend (Line) ---
    if time_series:
        st.subheader("Response Time Trend")
        import pandas as pd
        ts_df = pd.DataFrame(time_series)
        if not ts_df.empty and "date" in ts_df.columns:
            ts_df["date"] = pd.to_datetime(ts_df["date"])
            ts_df = ts_df.set_index("date")
            if "avg_response_time_ms" in ts_df.columns:
                st.line_chart(ts_df["avg_response_time_ms"])

    # --- Chart 2: Intent Distribution (Bar) ---
    if intents:
        st.subheader("Intent Distribution")
        import pandas as pd
        intent_df = pd.DataFrame(intents)
        if not intent_df.empty:
            intent_df = intent_df.set_index("intent")
            st.bar_chart(intent_df["count"])

    # --- Chart 3: Outcome Distribution (Donut approximation) ---
    st.subheader("Outcome Distribution")
    outcomes = {
        "Success": summary.get("success_count", 0),
        "Partial": summary.get("partial_count", 0),
        "Failure": summary.get("failure_count", 0),
        "Security Flagged": summary.get("flagged_count", 0),
    }
    total = sum(outcomes.values())
    if total > 0:
        for name, count in outcomes.items():
            pct = count / total * 100
            color = {"Success": "🟢", "Partial": "🟡", "Failure": "🔴", "Security Flagged": "🔴"}.get(name, "⚪")
            st.markdown(f"{color} **{name}:** {count} ({pct:.1f}%)")
    else:
        st.info("No data yet. Start chatting to see outcome distribution.")

    # --- Chart 4: Security Events over time ---
    if time_series:
        st.subheader("Daily Message Volume")
        import pandas as pd
        ts_df = pd.DataFrame(time_series)
        if not ts_df.empty and "date" in ts_df.columns:
            ts_df["date"] = pd.to_datetime(ts_df["date"])
            ts_df = ts_df.set_index("date")
            if "total_messages" in ts_df.columns:
                st.area_chart(ts_df["total_messages"])

    st.divider()

    # --- Recent Sessions Table ---
    st.subheader("Recent Sessions")
    sessions = fetch_sessions(cb_type, limit=20)
    if sessions:
        import pandas as pd
        sess_df = pd.DataFrame(sessions)
        display_cols = [c for c in ["session_id", "chatbot_type", "started_at", "outcome", "total_messages", "avg_confidence"] if c in sess_df.columns]
        if display_cols:
            st.dataframe(sess_df[display_cols], use_container_width=True)
    else:
        st.info("No sessions recorded yet.")

    st.divider()

    # --- Anomalies ---
    st.subheader("Anomaly Detection")
    anomalies = fetch_anomalies()
    if anomalies and anomalies.get("anomalies"):
        for a in anomalies["anomalies"]:
            st.warning(f"⚠️ {a.get('metric', 'Unknown')}: {a.get('message', '')}")
    else:
        st.success("No anomalies detected.")

    # --- Report Downloads ---
    st.divider()
    st.subheader("📥 Download Reports")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📄 Daily PDF"):
            try:
                resp = requests.get(f"{API_BASE}/reports/daily_pdf", timeout=30)
                if resp.status_code == 200:
                    st.download_button("Download", resp.content, "daily_report.pdf", "application/pdf")
                else:
                    st.error("Failed to generate daily report")
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("📄 Weekly PDF"):
            try:
                resp = requests.get(f"{API_BASE}/reports/weekly_pdf", timeout=30)
                if resp.status_code == 200:
                    st.download_button("Download", resp.content, "weekly_report.pdf", "application/pdf")
                else:
                    st.error("Failed to generate weekly report")
            except Exception as e:
                st.error(f"Error: {e}")

    with col3:
        if st.button("🔒 Security PDF"):
            try:
                resp = requests.get(f"{API_BASE}/reports/security_pdf", timeout=30)
                if resp.status_code == 200:
                    st.download_button("Download", resp.content, "security_report.pdf", "application/pdf")
                else:
                    st.error("Failed to generate security report")
            except Exception as e:
                st.error(f"Error: {e}")

    with col4:
        if st.button("📊 Full Excel"):
            try:
                resp = requests.get(f"{API_BASE}/reports/full_excel", timeout=30)
                if resp.status_code == 200:
                    st.download_button("Download", resp.content, "full_report.xlsx",
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    st.error("Failed to generate Excel report")
            except Exception as e:
                st.error(f"Error: {e}")
