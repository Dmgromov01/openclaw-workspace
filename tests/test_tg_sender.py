import importlib.util
from pathlib import Path


_SPEC = importlib.util.spec_from_file_location(
    "tg_sender_under_test", Path(__file__).parents[1] / "calendar" / "tg_sender.py"
)
tg_sender = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(tg_sender)


def test_recipient_key_normalizes_usernames():
    assert tg_sender._recipient_key("  @Trusted_User ") == "trusted_user"


def test_allowlist_fails_closed(monkeypatch):
    monkeypatch.setattr(tg_sender, "TG_ALLOWED_RECIPIENTS", frozenset())
    try:
        tg_sender._ensure_allowed("trusted_user")
    except RuntimeError as exc:
        assert "TG_ALLOWED_RECIPIENTS" in str(exc)
    else:
        raise AssertionError("missing allowlist must reject sends")


def test_allowlist_rejects_unknown_recipient(monkeypatch):
    monkeypatch.setattr(tg_sender, "TG_ALLOWED_RECIPIENTS", frozenset({"trusted_user"}))
    try:
        tg_sender._ensure_allowed("other_user")
    except RuntimeError as exc:
        assert "не входит" in str(exc)
    else:
        raise AssertionError("unknown recipients must be rejected")
