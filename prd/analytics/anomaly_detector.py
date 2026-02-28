"""Anomaly detection — Z-score based anomaly detection on analytics metrics.

How it works:
  1. Pulls a rolling time-series from the analytics SQLite database.
  2. For each metric (avg_response_time_ms, total_messages, failure_rate),
     calculates the mean and standard deviation over the configured window.
  3. Computes the Z-score of the most recent day's value.
  4. If |Z| ≥ threshold (default 2.0σ), the data point is flagged as an anomaly.

This module is called by the /analytics/anomalies FastAPI endpoint.
"""

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
    # Load anomaly detection settings from config.yaml → analytics section
    cfg = get_analytics_config()
    window_days = cfg.get("anomaly_window_days", 7)     # Number of days for the rolling baseline
    z_threshold = cfg.get("anomaly_zscore_threshold", 2.0)  # Z-score cutoff to flag an anomaly

    # Fetch extra days of history so the rolling window has enough data
    time_series = get_time_series(chatbot_type, days=window_days + 7)  # Extra days for context

    # Need at least 3 data points to compute a meaningful std deviation
    if not time_series or len(time_series) < 3:
        return {"anomalies": [], "metrics_checked": [], "message": "Not enough data for anomaly detection"}

    anomalies = []
    # These are the primary numeric metrics we check for spikes / dips
    metrics_to_check = ["avg_response_time_ms", "total_messages"]

    for metric in metrics_to_check:
        # Extract the metric's values from each day in the time series
        values = [row.get(metric, 0) or 0 for row in time_series]
        if not values or len(values) < 3:
            continue

        values_arr = np.array(values, dtype=float)
        mean = np.mean(values_arr)   # Average over the window
        std = np.std(values_arr)     # Standard deviation over the window

        if std == 0:
            continue  # All identical values → no deviation possible

        # Compare the LATEST day's value against the window's distribution
        latest = values_arr[-1]
        z_score = abs(latest - mean) / std  # How many std devs from the mean

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

    # --- Also check failure rate (derived metric = failure / total) ---
    success_vals = [row.get("success_count", 0) or 0 for row in time_series]
    failure_vals = [row.get("failure_count", 0) or 0 for row in time_series]
    total_vals = [s + f for s, f in zip(success_vals, failure_vals)]  # Total per day

    # Compute daily failure rate (0.0–1.0), guarding against division by zero
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
