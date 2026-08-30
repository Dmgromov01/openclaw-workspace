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
