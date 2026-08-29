"""Helpers for safely handling user-supplied upload names and paths."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

ALLOWED_EXTENSIONS = frozenset({".xlsx", ".xls", ".csv", ".pdf"})
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def safe_filename(original: str | None, max_length: int = 100) -> str:
    """Return a single, non-traversing filename suitable for local storage."""
    value = (original or "upload").replace("\\", "/")
    value = Path(value).name
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[^\w. -]", "_", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "_", value).strip("._ ")
    if not value or value in {".", ".."}:
        value = "upload"
    # Keep the extension when truncating long names.
    suffix = Path(value).suffix.lower()
    stem = Path(value).stem[: max(1, max_length - len(suffix))]
    return f"{stem}{suffix}"[:max_length]


def upload_path(root: Path, user_id: int | str, message_id: int | str,
                original: str | None) -> Path:
    """Build a unique path and assert that it remains below ``root``."""
    root = root.resolve()
    name = safe_filename(original)
    candidate = (root / f"{user_id}_{message_id}_{name}").resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("upload path escaped its storage directory") from exc
    return candidate
