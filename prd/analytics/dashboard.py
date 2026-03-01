"""Analytics Dashboard — Streamlit component with 5 KPI cards and 4 charts.

This module is imported and rendered inside the Streamlit chatbot UIs.
It fetches all data from the FastAPI backend REST endpoints (/analytics,
/analytics/sessions, /analytics/anomalies) rather than querying the DB
directly, so it works as a pure frontend component.

Sections rendered:
  1. KPI Cards      — Total Chats, Success Rate, Avg Response Time, CSAT, Security Events
  2. Line Chart     — Response time trend over time
  3. Bar Chart      — Intent distribution (which categories users ask about)
  4. Outcome Donut  — Success / Partial / Failure / Security Flagged breakdown
  5. Area Chart     — Daily message volume
  6. Sessions Table — Recent chat sessions with key metadata
  7. Anomalies      — Z-score anomaly warnings
  8. Report Downloads — Buttons to generate & download PDF/Excel reports
"""

import requests
import streamlit as st

# Base URL of the FastAPI backend (must be running on the same host)
API_BASE = "http://localhost:8000"


def fetch_analytics(chatbot_type: str = None, days: int = 30) -> dict:
    """Fetch aggregated analytics (KPIs + time-series + intents) from FastAPI."""
    try:
        params = {"days": days}
        if chatbot_type:
            params["chatbot_type"] = chatbot_type
        # GET /analytics returns summary, time_series, and intent_distribution
        resp = requests.get(f"{API_BASE}/analytics", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def fetch_sessions(chatbot_type: str = None, limit: int = 20) -> list:
    """Fetch a list of recent chat sessions from /analytics/sessions."""
    try:
        params = {"limit": limit}
        if chatbot_type:
            params["chatbot_type"] = chatbot_type
        resp = requests.get(f"{API_BASE}/analytics/sessions", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []  # Gracefully return empty on failure


def fetch_anomalies() -> dict:
    """Fetch Z-score anomaly detection results from /analytics/anomalies."""
    try:
        resp = requests.get(f"{API_BASE}/analytics/anomalies", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}  # Gracefully return empty on failure


def _render_filters():
    """Render chatbot type and time range filter controls. Returns (cb_type, days)."""
    col1, col2 = st.columns(2)
    with col1:
        chatbot_filter = st.selectbox("Chatbot Type", ["All", "microsite", "support"])
    with col2:
        days_filter = st.selectbox("Time Range", [7, 14, 30, 90], index=2)
    cb_type = None if chatbot_filter == "All" else chatbot_filter
    return cb_type, days_filter


def _render_kpi_cards(summary):
    """Render the 5 top-level KPI metric cards."""
    st.subheader("Key Performance Indicators")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    kpi1.metric("Total Chats", summary.get("total_sessions", 0))
    success_rate = summary.get("success_rate", 0)
    kpi2.metric("Success Rate", f"{success_rate:.1f}%")
    kpi3.metric("Avg Response Time", f"{summary.get('avg_response_time_ms', 0):.0f}ms")
    kpi4.metric("CSAT Score", f"{summary.get('csat', 3.0):.1f}/5.0")
    kpi5.metric("Security Events", summary.get("security_events", 0))

    st.divider()


def _render_response_time_chart(time_series):
    """Render response time trend line chart."""
    if not time_series:
        return
    st.subheader("Response Time Trend")
    import pandas as pd
    ts_df = pd.DataFrame(time_series)
    if not ts_df.empty and "date" in ts_df.columns:
        ts_df["date"] = pd.to_datetime(ts_df["date"])
        ts_df = ts_df.set_index("date")
        if "avg_response_time_ms" in ts_df.columns:
            st.line_chart(ts_df["avg_response_time_ms"])


def _render_intent_chart(intents):
    """Render intent distribution bar chart."""
    if not intents:
        return
    st.subheader("Intent Distribution")
    import pandas as pd
    intent_df = pd.DataFrame(intents)
    if not intent_df.empty:
        intent_df = intent_df.set_index("intent")
        st.bar_chart(intent_df["count"])


def _render_outcome_distribution(summary):
    """Render outcome distribution (success/partial/failure/flagged)."""
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
            color = {
                "Success": "\U0001f7e2",
                "Partial": "\U0001f7e1",
                "Failure": "\U0001f534",
                "Security Flagged": "\U0001f534",
            }.get(name, "\u26aa")
            st.markdown(f"{color} **{name}:** {count} ({pct:.1f}%)")
    else:
        st.info("No data yet. Start chatting to see outcome distribution.")


def _render_volume_chart(time_series):
    """Render daily message volume area chart."""
    if not time_series:
        return
    st.subheader("Daily Message Volume")
    import pandas as pd
    ts_df = pd.DataFrame(time_series)
    if not ts_df.empty and "date" in ts_df.columns:
        ts_df["date"] = pd.to_datetime(ts_df["date"])
        ts_df = ts_df.set_index("date")
        if "total_messages" in ts_df.columns:
            st.area_chart(ts_df["total_messages"])


def _render_sessions_table(cb_type):
    """Render the recent sessions table."""
    st.subheader("Recent Sessions")
    sessions = fetch_sessions(cb_type, limit=20)
    if sessions:
        import pandas as pd
        sess_df = pd.DataFrame(sessions)
        display_cols = [
            c for c in [
                "session_id", "chatbot_type", "started_at",
                "outcome", "total_messages", "avg_confidence",
            ] if c in sess_df.columns
        ]
        if display_cols:
            st.dataframe(sess_df[display_cols], use_container_width=True)
    else:
        st.info("No sessions recorded yet.")

    st.divider()


def _render_anomaly_alerts():
    """Render Z-score anomaly warnings."""
    st.subheader("Anomaly Detection")
    anomalies = fetch_anomalies()
    if anomalies and anomalies.get("anomalies"):
        for a in anomalies["anomalies"]:
            st.warning(
                f"\u26a0\ufe0f {a.get('metric', 'Unknown')}: {a.get('message', '')}")
    else:
        st.success("No anomalies detected.")


def _download_report_button(label, endpoint, filename, media_type):
    """Render a single report download button with error handling."""
    if st.button(label):
        try:
            resp = requests.get(f"{API_BASE}{endpoint}", timeout=30)
            if resp.status_code == 200:
                st.download_button("Download", resp.content, filename, media_type)
            else:
                st.error("Failed to generate report")
        except Exception as e:
            st.error(f"Error: {e}")


def _render_report_downloads():
    """Render the report download buttons section."""
    st.divider()
    st.subheader("\U0001f4e5 Download Reports")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        _download_report_button(
            "\U0001f4c4 Daily PDF", "/reports/daily_pdf",
            "daily_report.pdf", "application/pdf")

    with col2:
        _download_report_button(
            "\U0001f4c4 Weekly PDF", "/reports/weekly_pdf",
            "weekly_report.pdf", "application/pdf")

    with col3:
        _download_report_button(
            "\U0001f512 Security PDF", "/reports/security_pdf",
            "security_report.pdf", "application/pdf")

    with col4:
        _download_report_button(
            "\U0001f4ca Full Excel", "/reports/full_excel",
            "full_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def render_dashboard():
    """Render the full analytics dashboard as a Streamlit component.

    This is the main entry point called by the chatbot UIs to embed the
    analytics dashboard.  It draws filters, KPI cards, charts, session
    tables, anomaly alerts, and report download buttons.
    """
    st.header("\U0001f4ca Analytics Dashboard")

    # --- Filters: let the user narrow by chatbot type and time range ---
    cb_type, days_filter = _render_filters()

    # Fetch all analytics data from the FastAPI backend
    data = fetch_analytics(cb_type, days_filter)

    if "error" in data:
        st.error(f"Cannot fetch analytics: {data['error']}")
        return

    # Unpack the three sections returned by the /analytics endpoint
    summary = data.get("summary", {})
    time_series = data.get("time_series", [])
    intents = data.get("intent_distribution", [])

    _render_kpi_cards(summary)
    _render_response_time_chart(time_series)
    _render_intent_chart(intents)
    _render_outcome_distribution(summary)
    _render_volume_chart(time_series)

    st.divider()

    _render_sessions_table(cb_type)
    _render_anomaly_alerts()
    _render_report_downloads()
