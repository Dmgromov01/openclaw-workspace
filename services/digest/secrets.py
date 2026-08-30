"""Small helpers for loading OpenClaw credentials without duplicating lookup logic."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SECRET_FILES = (
    Path("/etc/openclaw/secrets.json"),
    Path("/root/.openclaw/secrets/secrets.json"),
    Path("/root/.openclaw/secrets.json"),
)


def _find_secret(value: Any, secret_id: str | None) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if secret_id:
            candidate = value.get(secret_id.lstrip("/"))
            if isinstance(candidate, str):
                return candidate
        for nested in value.values():
            found = _find_secret(nested, None)
            if found:
                return found
    return None


def read_secret_ref(value: Any) -> str | None:
    """Resolve a string or OpenClaw file-provider reference."""
    if isinstance(value, str):
        return value.strip() or None
    if not isinstance(value, dict):
        return None

    source = value.get("source")
    secret_id = value.get("id")
    if source == "file" and secret_id:
        path = Path(str(secret_id))
        try:
            if path.is_file():
                return path.read_text(encoding="utf-8").strip() or None
        except OSError:
            pass

    for secret_file in SECRET_FILES:
        try:
            if secret_file.is_file():
                found = _find_secret(json.loads(secret_file.read_text(encoding="utf-8")), str(secret_id) if secret_id else None)
                if found:
                    return found.strip()
        except (OSError, ValueError):
            continue
    return None


def deepseek_config() -> tuple[str | None, str]:
    """Return (API key, base URL) from the runtime OpenClaw config."""
    config_path = Path("/root/.openclaw/openclaw.json")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        provider = config.get("models", {}).get("providers", {}).get("deepseek", {})
        key = read_secret_ref(provider.get("apiKey"))
        base = str(provider.get("baseUrl", "https://api.deepseek.com/")).rstrip("/") + "/v1"
        return key, base
    except (OSError, ValueError, TypeError):
        return None, "https://api.deepseek.com/v1"
