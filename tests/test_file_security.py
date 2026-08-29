from pathlib import Path

import pytest

from bot.file_security import upload_path, safe_filename


def test_safe_filename_removes_traversal_and_control_chars():
    result = safe_filename("../../etc/passwd\\evil\nname.xlsx")
    assert "/" not in result
    assert "\\" not in result
    assert result.endswith(".xlsx")


def test_upload_path_stays_below_root_and_is_unique():
    root = Path("/tmp/openclaw-test-uploads")
    first = upload_path(root, 10, 1, "report.csv")
    second = upload_path(root, 10, 2, "report.csv")
    assert first.parent == root.resolve()
    assert first != second


def test_upload_path_rejects_no_escape_even_for_windows_input():
    path = upload_path(Path("/tmp/uploads"), "user", "message", "C:\\temp\\a.pdf")
    assert path.parent == Path("/tmp/uploads").resolve()
    assert path.name.endswith(".pdf")
