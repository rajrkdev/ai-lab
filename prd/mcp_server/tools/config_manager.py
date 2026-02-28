"""Configuration manager — Read/write config.yaml for LLM routing and system settings."""

import os
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.yaml"


def _load_yaml() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_yaml(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)


def get_config() -> dict:
    """Return full config dict."""
    return _load_yaml()


def get_llm_config() -> dict:
    return _load_yaml().get("llm_routing", {})


def get_security_config() -> dict:
    return _load_yaml().get("security", {})


def get_rag_config() -> dict:
    return _load_yaml().get("rag", {})


def get_embeddings_config() -> dict:
    return _load_yaml().get("embeddings", {})


def get_analytics_config() -> dict:
    return _load_yaml().get("analytics", {})


def update_config(mode: str = None, llm: str = None) -> dict:
    """Update LLM routing config. Returns updated config."""
    cfg = _load_yaml()
    if mode is not None:
        cfg["llm_routing"]["mode"] = mode
    if llm is not None:
        cfg["llm_routing"]["primary"] = llm
    _save_yaml(cfg)
    return {"status": "ok", "config": cfg["llm_routing"]}
