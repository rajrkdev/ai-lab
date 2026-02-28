"""Anomaly detection — Z-score based anomaly detection on analytics metrics."""

from typing import Dict, List

import numpy as np

from mcp_server.tools.analytics_logger import get_time_series
from mcp_server.tools.config_manager import get_analytics_config


def detect_anomalies(chatbot_type: str = None) -> Dict:
    """Run Z-score anomaly detection on key metrics.

    Uses a 7-day rolling window with 2σ threshold.

    Returns:
        anomalies: list of detected anomalies
        metrics_checked: list of metric names checked
    """
    cfg = get_analytics_config()
    window_days = cfg.get("anomaly_window_days", 7)
    z_threshold = cfg.get("anomaly_zscore_threshold", 2.0)

    time_series = get_time_series(chatbot_type, days=window_days + 7)  # Extra days for context

    if not time_series or len(time_series) < 3:
        return {"anomalies": [], "metrics_checked": [], "message": "Not enough data for anomaly detection"}

    anomalies = []
    metrics_to_check = ["avg_response_time_ms", "total_messages"]

    for metric in metrics_to_check:
        values = [row.get(metric, 0) or 0 for row in time_series]
        if not values or len(values) < 3:
            continue

        values_arr = np.array(values, dtype=float)
        mean = np.mean(values_arr)
        std = np.std(values_arr)

        if std == 0:
            continue

        # Check the most recent value
        latest = values_arr[-1]
        z_score = abs(latest - mean) / std

        if z_score >= z_threshold:
            direction = "above" if latest > mean else "below"
            anomalies.append({
                "metric": metric,
                "date": time_series[-1].get("date", "unknown"),
                "value": float(latest),
                "mean": round(float(mean), 2),
                "std": round(float(std), 2),
                "z_score": round(float(z_score), 2),
                "threshold": z_threshold,
                "message": f"{metric} is {z_score:.1f}σ {direction} the {window_days}-day mean ({mean:.1f} → {latest:.1f})",
            })

    # Also check failure rate if we have success/failure data
    success_vals = [row.get("success_count", 0) or 0 for row in time_series]
    failure_vals = [row.get("failure_count", 0) or 0 for row in time_series]
    total_vals = [s + f for s, f in zip(success_vals, failure_vals)]

    failure_rates = []
    for f, t in zip(failure_vals, total_vals):
        if t > 0:
            failure_rates.append(f / t)
        else:
            failure_rates.append(0.0)

    if len(failure_rates) >= 3:
        fr_arr = np.array(failure_rates, dtype=float)
        mean = np.mean(fr_arr)
        std = np.std(fr_arr)
        if std > 0:
            latest = fr_arr[-1]
            z_score = abs(latest - mean) / std
            if z_score >= z_threshold:
                anomalies.append({
                    "metric": "failure_rate",
                    "date": time_series[-1].get("date", "unknown"),
                    "value": round(float(latest), 3),
                    "mean": round(float(mean), 3),
                    "z_score": round(float(z_score), 2),
                    "message": f"Failure rate is {z_score:.1f}σ above normal ({mean:.1%} → {latest:.1%})",
                })

    return {
        "anomalies": anomalies,
        "metrics_checked": metrics_to_check + ["failure_rate"],
        "window_days": window_days,
        "z_threshold": z_threshold,
    }
