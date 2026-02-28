"""Configuration manager — Read/write config.yaml for LLM routing and system settings.

This module provides typed accessor functions for each section of config.yaml
(llm_routing, security, rag, embeddings, analytics).  Every tool and service
in the project reads its settings through these helpers so there is a single
source of truth.  The `update_config()` function also writes back changes,
enabling live LLM routing switches without a restart.
"""

import os
from pathlib import Path

import yaml

# Resolve the absolute path to config.yaml at the project root
# (this file lives at mcp_server/tools/config_manager.py, so go up twice)
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.yaml"


def _load_yaml() -> dict:
    """Read and parse config.yaml from disk."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_yaml(cfg: dict) -> None:
    """Write the full config dict back to config.yaml (overwrites entire file)."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Section accessors — each returns just one top-level key from the YAML.
# ---------------------------------------------------------------------------

def get_config() -> dict:
    """Return the full config dict (all sections)."""
    return _load_yaml()


def get_llm_config() -> dict:
    """Return the 'llm_routing' section (primary, fallback, classifier, etc.)."""
    return _load_yaml().get("llm_routing", {})


def get_security_config() -> dict:
    """Return the 'security' section (input + output validation settings)."""
    return _load_yaml().get("security", {})


def get_rag_config() -> dict:
    """Return the 'rag' section (top_k, chunk sizes, collection names, etc.)."""
    return _load_yaml().get("rag", {})


def get_embeddings_config() -> dict:
    """Return the 'embeddings' section (provider, model, dimensions)."""
    return _load_yaml().get("embeddings", {})


def get_analytics_config() -> dict:
    """Return the 'analytics' section (db_path, audit_log_path, anomaly settings)."""
    return _load_yaml().get("analytics", {})


def update_config(mode: str = None, llm: str = None) -> dict:
    """Update LLM routing config and persist to disk.

    Args:
        mode: New routing mode (e.g. 'auto' or a specific model name).
        llm:  Override the primary LLM model name.

    Returns:
        dict with 'status' and the updated llm_routing section.
    """
    cfg = _load_yaml()
    if mode is not None:
        cfg["llm_routing"]["mode"] = mode
    if llm is not None:
        cfg["llm_routing"]["primary"] = llm
    _save_yaml(cfg)
    return {"status": "ok", "config": cfg["llm_routing"]}
