"""Report generation — Daily PDF, Weekly PDF, Security PDF, Full Excel."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from mcp_server.tools.analytics_logger import (
    get_analytics_summary,
    get_intent_distribution,
    get_security_events,
    get_sessions_list,
    get_time_series,
)


def _make_temp_path(suffix: str) -> str:
    """Create a temp file path for report output."""
    return tempfile.mktemp(suffix=suffix, prefix="insurechat_report_")


def generate_daily_pdf() -> str:
    """Generate daily summary PDF. Returns file path."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    path = _make_temp_path(".pdf")
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=18)
    elements.append(Paragraph("InsureChat v3.0 — Daily Summary Report", title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    elements.append(Spacer(1, 24))

    # KPIs
    elements.append(Paragraph("Key Performance Indicators (Last 24 hours)", styles["Heading2"]))
    summary = get_analytics_summary(days=1)
    kpi_data = [
        ["Metric", "Value"],
        ["Total Sessions", str(summary.get("total_sessions", 0))],
        ["Total Messages", str(summary.get("total_messages", 0))],
        ["Success Rate", f"{summary.get('success_rate', 0):.1f}%"],
        ["Avg Confidence", f"{summary.get('avg_confidence', 0):.3f}"],
        ["Avg Response Time", f"{summary.get('avg_response_time_ms', 0):.0f}ms"],
        ["Security Events", str(summary.get("security_events", 0))],
        ["CSAT Score", f"{summary.get('csat', 3.0):.1f}/5.0"],
    ]
    kpi_table = Table(kpi_data, colWidths=[3 * inch, 2 * inch])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2196F3")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 24))

    # Outcome Distribution
    elements.append(Paragraph("Outcome Distribution", styles["Heading2"]))
    outcome_data = [
        ["Outcome", "Count"],
        ["Success", str(summary.get("success_count", 0))],
        ["Partial", str(summary.get("partial_count", 0))],
        ["Failure", str(summary.get("failure_count", 0))],
        ["Security Flagged", str(summary.get("flagged_count", 0))],
    ]
    outcome_table = Table(outcome_data, colWidths=[3 * inch, 2 * inch])
    outcome_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(outcome_table)
    elements.append(Spacer(1, 24))

    # Top Intents
    elements.append(Paragraph("Top Intents", styles["Heading2"]))
    intents = get_intent_distribution(days=1)
    if intents:
        intent_data = [["Intent", "Count"]]
        for i in intents[:10]:
            intent_data.append([i["intent"], str(i["count"])])
        intent_table = Table(intent_data, colWidths=[3 * inch, 2 * inch])
        intent_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FF9800")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(intent_table)
    else:
        elements.append(Paragraph("No intent data for the last 24 hours.", styles["Normal"]))

    elements.append(Spacer(1, 24))

    # Security Summary
    elements.append(Paragraph("Security Summary", styles["Heading2"]))
    sec_events = get_security_events(limit=10)
    if sec_events:
        sec_data = [["Timestamp", "Type", "Severity", "Chatbot"]]
        for ev in sec_events[:10]:
            sec_data.append([
                ev.get("timestamp", "")[:19],
                ev.get("event_type", ""),
                ev.get("severity", ""),
                ev.get("chatbot_type", ""),
            ])
        sec_table = Table(sec_data, colWidths=[2.5 * inch, 1.5 * inch, 1 * inch, 1 * inch])
        sec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F44336")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(sec_table)
    else:
        elements.append(Paragraph("No security events in the last 24 hours.", styles["Normal"]))

    doc.build(elements)
    return path


def generate_weekly_pdf() -> str:
    """Generate weekly trends PDF. Returns file path."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    path = _make_temp_path(".pdf")
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("InsureChat v3.0 — Weekly Trends Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    elements.append(Spacer(1, 24))

    # 7-day KPIs
    elements.append(Paragraph("7-Day KPI Summary", styles["Heading2"]))
    summary = get_analytics_summary(days=7)
    kpi_data = [
        ["Metric", "Value"],
        ["Total Sessions", str(summary.get("total_sessions", 0))],
        ["Success Rate", f"{summary.get('success_rate', 0):.1f}%"],
        ["Avg Response Time", f"{summary.get('avg_response_time_ms', 0):.0f}ms"],
        ["Security Events", str(summary.get("security_events", 0))],
    ]
    table = Table(kpi_data, colWidths=[3 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2196F3")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 24))

    # Daily breakdown
    elements.append(Paragraph("Daily Breakdown", styles["Heading2"]))
    ts = get_time_series(days=7)
    if ts:
        ts_data = [["Date", "Messages", "Avg Confidence", "Avg Response Time (ms)"]]
        for row in ts:
            ts_data.append([
                row.get("date", ""),
                str(row.get("total_messages", 0)),
                f"{row.get('avg_confidence', 0):.3f}",
                f"{row.get('avg_response_time_ms', 0):.0f}",
            ])
        ts_table = Table(ts_data, colWidths=[1.5 * inch, 1.2 * inch, 1.5 * inch, 2 * inch])
        ts_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(ts_table)
    else:
        elements.append(Paragraph("No data for the last 7 days.", styles["Normal"]))

    doc.build(elements)
    return path


def generate_security_pdf() -> str:
    """Generate security incidents PDF. Returns file path."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    path = _make_temp_path(".pdf")
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("InsureChat v3.0 — Security Incidents Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    elements.append(Spacer(1, 24))

    events = get_security_events(limit=100)

    if events:
        elements.append(Paragraph(f"Total Security Events: {len(events)}", styles["Heading2"]))
        elements.append(Spacer(1, 12))

        sec_data = [["Timestamp", "Event Type", "Severity", "Chatbot", "Details"]]
        for ev in events:
            sec_data.append([
                ev.get("timestamp", "")[:19],
                ev.get("event_type", ""),
                ev.get("severity", ""),
                ev.get("chatbot_type", ""),
                str(ev.get("details", ""))[:50],
            ])
        sec_table = Table(sec_data, colWidths=[1.5 * inch, 1 * inch, 0.8 * inch, 0.8 * inch, 2 * inch])
        sec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F44336")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF3F0")]),
        ]))
        elements.append(sec_table)
    else:
        elements.append(Paragraph("No security events recorded.", styles["Heading2"]))

    doc.build(elements)
    return path


def generate_full_excel() -> str:
    """Generate full analytics Excel with 4 sheets. Returns file path."""
    import json

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    path = _make_temp_path(".xlsx")
    wb = Workbook()

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2196F3", end_color="2196F3", fill_type="solid")

    def style_header(ws, cols):
        for col_idx, header in enumerate(cols, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

    # Sheet 1: Summary
    ws1 = wb.active
    ws1.title = "Summary"
    summary = get_analytics_summary(days=30)
    style_header(ws1, ["Metric", "Value"])
    for i, (k, v) in enumerate(summary.items(), 2):
        ws1.cell(row=i, column=1, value=k)
        ws1.cell(row=i, column=2, value=str(v))
    ws1.column_dimensions["A"].width = 25
    ws1.column_dimensions["B"].width = 20

    # Sheet 2: Chat Details
    ws2 = wb.create_sheet("Chat Details")
    sessions = get_sessions_list(limit=500)
    headers2 = ["session_id", "chatbot_type", "started_at", "outcome", "total_messages", "avg_confidence", "avg_response_time_ms"]
    style_header(ws2, headers2)
    for i, sess in enumerate(sessions, 2):
        for j, h in enumerate(headers2, 1):
            ws2.cell(row=i, column=j, value=str(sess.get(h, "")))
    for j in range(len(headers2)):
        ws2.column_dimensions[chr(65 + j)].width = 20

    # Sheet 3: Security Events
    ws3 = wb.create_sheet("Security Events")
    sec_events = get_security_events(limit=500)
    headers3 = ["timestamp", "event_type", "severity", "chatbot_type", "details"]
    style_header(ws3, headers3)
    for i, ev in enumerate(sec_events, 2):
        for j, h in enumerate(headers3, 1):
            val = ev.get(h, "")
            if isinstance(val, dict):
                val = json.dumps(val)
            ws3.cell(row=i, column=j, value=str(val)[:200])
    for j in range(len(headers3)):
        ws3.column_dimensions[chr(65 + j)].width = 22

    # Sheet 4: Intent Breakdown
    ws4 = wb.create_sheet("Intent Breakdown")
    intents = get_intent_distribution(days=30)
    style_header(ws4, ["Intent", "Count"])
    for i, item in enumerate(intents, 2):
        ws4.cell(row=i, column=1, value=item.get("intent", ""))
        ws4.cell(row=i, column=2, value=item.get("count", 0))
    ws4.column_dimensions["A"].width = 25
    ws4.column_dimensions["B"].width = 15

    wb.save(path)
    return path
