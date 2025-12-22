"""Central memory configuration loader.

Reads configs/memory_config.json and overlays sane defaults.
Provides a cached getter to avoid repeated disk access.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

# Defaults used when file or fields are missing
DEFAULT_MEMORY_CONFIG: Dict[str, Any] = {
    "threshold_warning": 0.75,         # warn when RAM usage >= 75%
    "threshold_critical": 0.90,        # critical when RAM usage >= 90%
    "check_interval": 0.5,             # seconds between probe checks
    "gc_threshold": 0.85,              # trigger gc when usage >= 85%
    "aggressive_threshold": 0.85,      # use aggressive cleanup when >=85%
    "log_level": "INFO",
    "auto_inject": False,
    # Settings for memory pressurer / guard helpers (optional)
    "pressurer": {
        "safety_margin_mb": 400,       # try to keep this margin free
        "monitor_interval": 0.5,
        "threshold_warning": 0.75,
        "threshold_critical": 0.90,
    },
}

_CONFIG_PATH = Path("configs/memory_config.json")
_MEMORY_CONFIG_CACHE: Dict[str, Any] | None = None


def _deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge_dicts(out[k], v)
        else:
            out[k] = v
    return out


def _load_from_disk() -> Dict[str, Any]:
    if not _CONFIG_PATH.exists():
        return dict(DEFAULT_MEMORY_CONFIG)
    try:
        with _CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f) or {}
        return _deep_merge_dicts(DEFAULT_MEMORY_CONFIG, data)
    except Exception:
        # On any error, fall back to defaults (be conservative)
        return dict(DEFAULT_MEMORY_CONFIG)


def get_memory_config(refresh: bool = False) -> Dict[str, Any]:
    """Get memory config (cached by default).

    Args:
        refresh: when True, reload from disk.
    """
    global _MEMORY_CONFIG_CACHE
    if refresh or _MEMORY_CONFIG_CACHE is None:
        _MEMORY_CONFIG_CACHE = _load_from_disk()
    return _MEMORY_CONFIG_CACHE


def reload_memory_config() -> Dict[str, Any]:
    """Force reloading config from disk and update cache."""
    return get_memory_config(refresh=True)

