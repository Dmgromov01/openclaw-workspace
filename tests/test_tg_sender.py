import importlib.util
from pathlib import Path


_SPEC = importlib.util.spec_from_file_location(
    "bot_sender_under_test", Path(__file__).parents[1] / "calendar" / "bot_sender.py"
)
bot_sender = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(bot_sender)


def test_send_text_targets_owner(monkeypatch):
    calls = []

    def fake_api(method, **params):
        calls.append((method, params))
        return {"ok": True, "result": {"message_id": 1}}

    monkeypatch.setattr(bot_sender, "_api", fake_api)
    assert bot_sender.send_text_to_owner("hello") == "OK message_id=1"
    assert calls == [
        (
            "sendMessage",
            {"chat_id": bot_sender.OWNER_CHAT_ID, "text": "hello", "parse_mode": "HTML"},
        )
    ]


def test_send_text_does_not_fallback_on_non_html_error(monkeypatch):
    calls = []

    def fake_api(method, **params):
        calls.append((method, params))
        raise RuntimeError("Telegram API 401")

    monkeypatch.setattr(bot_sender, "_api", fake_api)
    try:
        bot_sender.send_text_to_owner("hello")
    except RuntimeError as exc:
        assert "401" in str(exc)
    else:
        raise AssertionError("non-400 Telegram errors must propagate")
    assert len(calls) == 1
