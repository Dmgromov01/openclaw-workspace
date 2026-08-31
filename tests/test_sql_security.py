import duckdb
import pytest

from skills.sql_security import validate_read_only_query


def test_allows_select():
    assert validate_read_only_query("SELECT * FROM sales") == "SELECT * FROM sales"


@pytest.mark.parametrize("query", [
    "DELETE FROM sales",
    "SELECT * FROM read_csv('secret.csv')",
    "SELECT 1; DROP TABLE sales",
    "INSTALL httpfs",
])
def test_rejects_unsafe_queries(query):
    with pytest.raises(ValueError):
        validate_read_only_query(query)


@pytest.mark.parametrize("query", [
    # Комментарии, разрывающие токены и прячущие запрещённые операции.
    "SELECT * FROM read_csv('secret.csv') -- обход",
    "SELECT * FROM read_csv('secret.csv') /* обход */",
    "SELECT/*x*/1;--\nDROP TABLE sales",
    "SELECT * FROM sales WHERE 1=1 --\nDELETE FROM sales",
    # Юникод-кавычки и юникод-пробелы в именах функций.
    "SELECT * FROM read\u00a0csv('secret.csv')",
    "SELECT * FROM \u201cread_csv\u201d('secret.csv')",
    "SELECT * FROM read_csv(\u2018secret.csv\u2019)",
    # Вложенные вызовы файловых функций.
    "SELECT * FROM (SELECT * FROM read_csv('secret.csv'))",
    "SELECT * FROM parquet_scan((SELECT 'x'))",
    "SELECT * FROM glob('*.csv')",
])
def test_rejects_bypass_attempts(query):
    """Обходы regex-блэклиста должны отклоняться валидатором."""
    with pytest.raises(ValueError):
        validate_read_only_query(query)


@pytest.mark.parametrize("query", [
    "SELECT * FROM read_csv('secret.csv')",
    "SELECT * FROM glob('*.csv')",
    "SELECT * FROM parquet_scan('/etc/passwd')",
    "SELECT * FROM sqlite_scan('/etc/passwd')",
])
def test_duckdb_engine_rejects_file_access_even_if_validator_missed(query):
    """Второй слой: enable_external_access=false режет файловый доступ на движке.

    Даже если regex-валидатор когда-нибудь пропустит обход, DuckDB сам не даст
    прочитать файлы. Это тест-страховка, а не приглашение ослаблять валидатор.
    """
    conn = duckdb.connect(database=":memory:")
    conn.execute("SET enable_external_access=false")
    try:
        with pytest.raises(duckdb.Error):
            conn.execute(query)
    finally:
        conn.close()
