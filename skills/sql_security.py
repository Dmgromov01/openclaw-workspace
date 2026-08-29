"""Safe SQL validation for in-memory spreadsheet analysis."""
from __future__ import annotations

import re

_FORBIDDEN = re.compile(
    r"\b(?:attach|copy|create|delete|drop|export|import|insert|install|load|pragma|read_csv|read_json|read_parquet|replace|select\s+\*\s+from\s+read_|update|vacuum|write_csv)\b",
    re.IGNORECASE,
)


def validate_read_only_query(query: str) -> str:
    """Allow one read-only query and reject file access or mutating statements."""
    value = query.strip().rstrip(";").strip()
    if not value or ";" in value:
        raise ValueError("разрешён только один SQL-запрос")
    if not re.match(r"^(?:select|with)\b", value, re.IGNORECASE):
        raise ValueError("разрешены только SELECT/CTE-запросы")
    if _FORBIDDEN.search(value):
        raise ValueError("запрос содержит запрещённую операцию")
    return value
