import importlib.util
from datetime import datetime
from pathlib import Path


_SPEC = importlib.util.spec_from_file_location(
    "gcal_reader_under_test", Path(__file__).parents[1] / "calendar" / "gcal_reader.py"
)
gcal = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(gcal)


def test_as_local_converts_utc_to_moscow():
    assert gcal.as_local("2026-08-29T09:00:00Z").strftime("%H:%M") == "12:00"


def test_event_date_supports_all_day_events():
    event = {"start": {"date": "2026-08-29"}, "end": {"date": "2026-08-30"}}
    assert gcal.event_date(event).isoformat() == "2026-08-29"


def test_parse_event_datetime_preserves_explicit_offset():
    parsed = gcal.parse_event_datetime("2026-08-29T09:00:00+00:00")
    assert parsed == datetime(2026, 8, 29, 12, 0, tzinfo=gcal.TZ)
