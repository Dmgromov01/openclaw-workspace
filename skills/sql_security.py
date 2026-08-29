"""Safe SQL validation for in-memory spreadsheet analysis."""
from __future__ import annotations

import re

# DuckDB exposes files through table functions and shorthand string paths.  A
# read-only SELECT is not safe if it can make the database read arbitrary local
# files or load extensions, so reject those forms before execution.
_FORBIDDEN = re.compile(
    r"(?:"
    r"\b(?:attach|copy|create|delete|drop|export|import|insert|install|load|pragma|replace|update|vacuum)\b"
    r"|\b(?:read_(?:csv|json|parquet)(?:_auto)?|parquet_scan|glob|sqlite_scan|postgres_scan)\s*\("
    r"|\bselect\s+\*\s+from\s+read_"
    r"|\bfrom\s+(?:'[^']*'|\"[^\"]*\")"
    r"|\b(?:read_csv|read_json|read_parquet|write_csv)\b"
    r")",
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
        raise ValueError("запрос содержит запрещённую операцию или доступ к файлам")
    return value
