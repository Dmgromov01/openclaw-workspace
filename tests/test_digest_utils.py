from datetime import datetime, timezone

from services.digest.digest_utils import clip, extract_rss_titles


def test_clip_keeps_limit_and_word_boundary():
    result = clip("one two three four", 10)
    assert result.endswith("…")
    assert len(result) <= 10
    assert result == "one two…"


def test_extract_rss_titles_filters_old_items_and_sorts_newest_first():
    data = """<?xml version="1.0"?><rss><channel>
      <item><title>Old story with enough words</title><pubDate>Wed, 01 Jan 2020 00:00:00 GMT</pubDate></item>
      <item><title>Newest story with enough words</title><pubDate>Wed, 01 Jan 2030 00:00:00 GMT</pubDate></item>
      <item><title>Story without a date with enough words</title></item>
    </channel></rss>"""
    result = extract_rss_titles(data, hours=2, limit=10)
    assert [title for title, _ in result] == [
        "Newest story with enough words",
        "Story without a date with enough words",
    ]
    assert result[0][1] == datetime(2030, 1, 1, tzinfo=timezone.utc)
