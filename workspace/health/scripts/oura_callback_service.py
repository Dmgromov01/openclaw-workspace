#!/usr/bin/env python3
"""Oura OAuth2 callback service (loopback only).

Receives the redirect from https://hub.gbkz.uk/?code=...&state=..., validates
the CSRF state, exchanges the code for tokens and stores them. Never prints or
logs secrets; logs the authorization code length only.

Environment:
    OURA_CALLBACK_HOST   bind host            (default 127.0.0.1)
    OURA_CALLBACK_PORT   bind port            (default 8092)

Exposed to the world through nginx; see deploy/nginx-hub-oura.snippet.
"""
from __future__ import annotations

import html
import json
import os
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import oura_auth as oa

HOST = os.environ.get("OURA_CALLBACK_HOST", "127.0.0.1")
PORT = int(os.environ.get("OURA_CALLBACK_PORT", "8092"))

# Single-flight background sync; poll progress through /sync/status.
_SYNC_STATE: dict = {"running": False, "started_at": None, "finished_at": None,
                     "result": None, "error": None}

PAGE = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Oura - {title}</title>
<style>body{{font-family:-apple-system,system-ui,sans-serif;max-width:34rem;margin:12vh auto;padding:0 1.25rem;line-height:1.5}}
h1{{font-size:1.35rem;margin:0 0 .75rem}}code{{background:#f2f2f7;padding:.1rem .35rem;border-radius:.25rem}}
.ok{{color:#0a7d32}} .bad{{color:#b3261e}} ul{{padding-left:1.1rem}}</style></head>
<body><h1 class="{cls}">{title}</h1>{body}</body></html>"""


def page(title: str, body: str, cls: str = "") -> bytes:
    return PAGE.format(title=html.escape(title), body=body, cls=cls).encode("utf-8")


def error_page(title: str, lines: list) -> bytes:
    items = "".join("<li>" + html.escape(str(x)) + "</li>" for x in lines)
    return page(title, "<ul>" + items + "</ul>", "bad")


class Handler(BaseHTTPRequestHandler):
    server_version = "oura-callback/1.0"

    def log_message(self, fmt, *args):
        # Never let code/state/iss reach the journal: strip the query string.
        msg = fmt % args
        if "?" in msg and " HTTP/" in msg:
            pre, _, post = msg.partition(" HTTP/")
            msg = pre.split("?")[0] + "?<redacted> HTTP/" + post
        sys.stderr.write("[oura-callback] " + msg + "\n")

    def _send(self, status: int, payload: bytes, ctype: str = "text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        if parsed.path.rstrip("/") == "/healthz":
            self._send(200, json.dumps({"ok": True}).encode("utf-8"), "application/json")
            return

        # Live end-to-end proof: API v2 before refresh, a forced refresh, then API
        # v2 again with the rotated token. Loopback only (nginx routes just /?code=).
        if parsed.path.rstrip("/") == "/verify":
            env = oa.read_env()
            report = {"stages": [], "granted_scope": env.get("OURA_SCOPE", "")}

            def api_stage(label):
                results = []
                sd = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 30 * 86400))
                ed = time.strftime("%Y-%m-%d", time.gmtime())
                d_range = {"start_date": sd, "end_date": ed}
                dt_range = {"start_datetime": sd + "T00:00:00+00:00",
                            "end_datetime": ed + "T00:00:00+00:00"}
                for name, path, params in (
                    ("personal_info", "personal_info", None),
                    ("daily_activity", "daily_activity", d_range),
                    ("daily_cardiovascular_age", "daily_cardiovascular_age", d_range),
                    ("daily_readiness", "daily_readiness", d_range),
                    ("daily_resilience", "daily_resilience", d_range),
                    ("daily_sleep", "daily_sleep", d_range),
                    ("daily_spo2", "daily_spo2", d_range),
                    ("daily_stress", "daily_stress", d_range),
                    ("enhanced_tag", "enhanced_tag", d_range),
                    ("heartrate", "heartrate", dt_range),
                    ("rest_mode_period", "rest_mode_period", d_range),
                    ("ring_configuration", "ring_configuration", None),
                    ("session", "session", d_range),
                    ("sleep", "sleep", d_range),
                    ("sleep_time", "sleep_time", d_range),
                    ("tag", "tag", d_range),
                    ("vO2_max", "vO2_max", d_range),
                    ("workout", "workout", d_range),
                ):
                    try:
                        data = oa.api_get_json(path, env, params)
                        items = len(data.get("data", [])) if isinstance(data, dict) else 0
                        results.append({"endpoint": name, "ok": True, "items": items})
                    except oa.OuraOAuthError as exc:
                        results.append({"endpoint": name, "ok": False, "status": exc.status,
                                        "diagnosis": exc.diagnosis})
                report["stages"].append({"stage": label, "results": results})

            api_stage("before_refresh")
            try:
                before = env.get("OURA_ACCESS_TOKEN", "")
                oa.ensure_access_token(env, force=True)
                report["refresh"] = {
                    "ok": True,
                    "expires_at": env.get("OURA_TOKEN_EXPIRES_AT"),
                    "access_token_rotated": env.get("OURA_ACCESS_TOKEN", "") != before,
                }
            except oa.OuraOAuthError as exc:
                report["refresh"] = {"ok": False, "status": exc.status, "diagnosis": exc.diagnosis}
            api_stage("after_refresh")
            report["ok"] = bool(report["refresh"].get("ok")) and all(
                r["ok"] for s in report["stages"] for r in s["results"])
            self._send(200, json.dumps(report, ensure_ascii=False).encode("utf-8"), "application/json")
            return

        if parsed.path.rstrip("/") == "/sync":
            try:
                days = int((query.get("days") or ["30"])[0])
            except ValueError:
                days = 30
            if _SYNC_STATE.get("running"):
                self._send(202, json.dumps({"ok": True, "running": True,
                                            "hint": "already running; poll /sync/status"}).encode("utf-8"),
                           "application/json")
                return
            import threading

            def worker():
                _SYNC_STATE.update(running=True, started_at=time.time(),
                                   finished_at=None, result=None, error=None)
                try:
                    import oura_sync
                    _SYNC_STATE["result"] = oura_sync.sync_all(days)
                except Exception as exc:
                    _SYNC_STATE["error"] = type(exc).__name__ + ": " + str(exc)[:200]
                finally:
                    _SYNC_STATE["running"] = False
                    _SYNC_STATE["finished_at"] = time.time()

            threading.Thread(target=worker, daemon=True).start()
            self._send(202, json.dumps({"ok": True, "running": True, "days": days}).encode("utf-8"),
                       "application/json")
            return

        if parsed.path.rstrip("/") in ("/sync/status", "/stats"):
            try:
                import oura_sync
                stats = oura_sync.raw_stats()
            except Exception as exc:
                stats = {"error": type(exc).__name__ + ": " + str(exc)[:200]}
            payload = dict(_SYNC_STATE)
            payload["stats"] = stats
            self._send(200, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json")
            return

        def one(name):
            values = query.get(name)
            return values[0] if values else ""

        err = one("error")
        code = one("code")
        state = one("state")
        print("[oura-callback] GET path=" + parsed.path + " code_present=" + str(bool(code)) +
              " code_length=" + str(len(code)) + " state_present=" + str(bool(state)) +
              " error=" + (err or "-"), file=sys.stderr)

        if err:
            self._send(400, error_page("Oura: отказ в доступе", [
                "Oura вернула error=" + err,
                "error_description=" + (one("error_description") or "-"),
                "Обмен кода не выполнялся. Повтори авторизацию заново.",
            ]))
            return

        if not code or not state:
            self._send(400, error_page("Oura callback: не хватает параметров", [
                "Ожидались code и state в query string.",
                "Возможно, redirect_uri в приложении Oura отличается.",
            ]))
            return

        saved = oa.consume_state(state)
        if saved is None:
            self._send(400, error_page("Oura callback: state не прошёл проверку", [
                "State неизвестен, уже использован или истёк (TTL " + str(oa.STATE_TTL_SECONDS) + " c).",
                "Запусти oura_oauth_exchange.py --authorize-url и открой свежую ссылку.",
            ]))
            return

        env = oa.read_env()
        client_id = env.get("OURA_CLIENT_ID", "") or ""
        client_secret = env.get("OURA_CLIENT_SECRET", "") or ""
        redirect_uri = saved.get("redirect_uri") or env.get("OURA_REDIRECT_URI") or oa.DEFAULT_REDIRECT_URI
        if not client_id or not client_secret:
            self._send(500, error_page("Oura callback: нет учётных данных клиента", [
                "Сначала на хосте: python3 oura_oauth_exchange.py --set-credentials",
                "Затем повтори авторизацию (нужен новый code).",
            ]))
            return

        try:
            tokens = oa.exchange_code(code, client_id, client_secret, redirect_uri)
        except oa.OuraOAuthError as exc:
            self._send(400, error_page("Oura: не удалось обменять код", [
                "HTTP " + str(exc.status) + " " + str(exc.code),
                exc.description,
                exc.diagnosis,
                "Код одноразовый: получи новый через --authorize-url.",
            ]))
            return

        oa.save_tokens(env, tokens)
        env.setdefault("OURA_CLIENT_ID", client_id)
        env["OURA_REDIRECT_URI"] = redirect_uri
        oa.write_env(env)
        expires = int(env.get("OURA_TOKEN_EXPIRES_AT", "0") or 0)
        self._send(200, page("Oura подключён", (
            "<p>Токены получены и сохранены (<code>" + html.escape(str(oa.ENV_PATH)) + "</code>, chmod 600).</p>"
            "<ul><li>token_type: " + html.escape(str(env.get("OURA_TOKEN_TYPE", ""))) + "</li>"
            "<li>scope: " + html.escape(str(env.get("OURA_SCOPE", ""))) + "</li>"
            "<li>access_token до: " + html.escape(time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(expires))) + "</li>"
            "<li>refresh_token: " + ("есть" if env.get("OURA_REFRESH_TOKEN") else "нет") + "</li></ul>"
            "<p>Можно закрыть страницу.</p>"
        ), "ok"))


def main() -> int:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print("[oura-callback] listening on " + HOST + ":" + str(PORT), file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
