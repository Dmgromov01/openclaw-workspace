# Oura OAuth2 integration - deployment notes

## Files

    scripts/oura_auth.py              OAuth2 core (exchange, refresh, state, API v2, diagnostics)
    scripts/oura_oauth_exchange.py    CLI: authorize URL, code exchange, credentials, --oauth-check, --api-check
    scripts/oura_callback_service.py  loopback callback receiver (:8092)
    scripts/oura_sync.py              data sync (refresh delegated to oura_auth)
    deploy/oura-callback.service      systemd user unit for the callback receiver
    deploy/nginx-hub-oura.snippet     nginx change routing /?code=... to :8092

## Why the old flow failed (verified against the live API)

    form body + valid client_id + wrong secret  -> 401 invalid_client
    extra/duplicate parameter (PKCE code_verifier,
        duplicated client_id)                   -> 400 invalid_request
    JSON body instead of form-encoded           -> 400 "Bad Request"

The 400 invalid_request means: an extra or duplicated parameter. Oura does NOT
support PKCE, so a leftover .pkce_verifier plus a code_verifier parameter
produces exactly that error. Additionally an authorization code is single-use:
re-running the exchange with the same code always fails.

## Activation (owner, on the host)

1. Credentials (once, hidden prompt, stored 0600):

       cd /root/openclaw/workspace/health/scripts
       python3 oura_oauth_exchange.py --set-credentials

2. Callback receiver:

       cp deploy/oura-callback.service ~/.config/systemd/user/
       systemctl --user daemon-reload
       systemctl --user enable --now oura-callback

3. nginx: apply deploy/nginx-hub-oura.snippet, then

       nginx -t && systemctl reload nginx

4. Authorize (one-time consent). Prints a fresh URL with a new CSRF state:

       python3 oura_oauth_exchange.py --authorize-url

   Open the URL, approve. Oura redirects to https://hub.gbkz.uk/?code=...&state=...
   and the callback service exchanges the code, stores the tokens, shows a page.

5. Verify:

       python3 oura_oauth_exchange.py --oauth-check
       python3 oura_oauth_exchange.py --api-check

## Scopes

    personal, daily, heartrate, workout, session, spo2Daily

(spo2Daily is the exact Oura scope name; note the spelling.)

## Token storage

    /root/openclaw/workspace/health/.env   chmod 600
    OURA_CLIENT_ID, OURA_CLIENT_SECRET, OURA_ACCESS_TOKEN, OURA_REFRESH_TOKEN,
    OURA_TOKEN_EXPIRES_AT, OURA_TOKENS_OBTAINED_AT, OURA_SCOPE, OURA_REDIRECT_URI

Refresh tokens are single-use: every refresh rotates and persists the new one.


## Analytics layer (18 collections)

    scripts/analytics.py        normalize all 18 collections -> daily_facts, then stats pack
    scripts/first_analysis.py   Deep Baseline Analysis (run FIRST, once)
    scripts/morning_report.py   short operational morning report
    scripts/weekly_report.py    --scope weekly | monthly

Order of operations:

    cd /root/openclaw/workspace/health
    python3 scripts/first_analysis.py      # baseline + observations seed
    python3 scripts/morning_report.py      # then daily
    python3 scripts/weekly_report.py --scope weekly

Outputs: analysis/baseline.json, analysis/current.json, analysis/weekly.json,
analysis/monthly.json, analysis/morning.md, memory/observations.md.

## Automations (systemd user timers, Europe/Moscow)

    health-morning   07:35 daily    sync 7d  + morning report
    health-weekly    Sun 10:00      sync 14d + weekly report
    health-monthly   1st 10:30      sync 45d + monthly report

Install (owner, on the host):

    cp /root/openclaw/workspace/health/deploy/health-*.service ~/.config/systemd/user/
    cp /root/openclaw/workspace/health/deploy/health-*.timer   ~/.config/systemd/user/
    systemctl --user daemon-reload
    systemctl --user enable --now health-morning.timer health-weekly.timer health-monthly.timer
    systemctl --user list-timers 'health-*'

Host runs in UTC; the timers carry an explicit Europe/Moscow zone, so 07:35 MSK
= 04:35 UTC. Logs: analysis/automation.log and analysis/automation.err.
