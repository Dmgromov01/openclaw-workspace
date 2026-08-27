# Промпт боту @Dmbotmy_bot — run6 (скопировать целиком)

Ты OpenClaw-агент **main** на этой машине. Хозяин Дмитрий (tg 1916536646) прямо сейчас разрешил этот прогон. Не пиши хаб заново. Не печатай секреты, токены, ключи, содержимое .env / openclaw.json / secrets.json. Не коммить секреты.

Репо workspace уже обновлён на GitHub: `Dmgromov01/openclaw-workspace` ветка main. Сначала подтяни, потом делай.

Цель run6 (всё за один проход, потом короткий отчёт):
1. Снять апрувы exec у агента (больше никаких /approve).
2. Gateway как **system**-юнит, старый --user stop+disable.
3. linger root.
4. Watchdog :18789 и :8765 (3 провала → restart, алерт HubAlertsbot, антишторм 1 мин).
5. Выжечь Google из LLM/vision/fallback. Фото = DeepSeek Vision. Без CLI media.
6. Не трогать: код хаба, ufw, zram, Parallel, Context7, GitHub MCP, агент hub (tools.allow=[]).

---

## 0) Апрувы — СРАЗУ, это главное

Сейчас узкий allowlist + ask=on-miss → команды висят и бот «мёртв». Хозяин сказал: апрувы убрать.

Порядок:

A. Если этот самый прогон упрётся в /approve на `openclaw` — это **последний** апрув. Хозяин нажмёт allow-always. Дальше апрувов быть не должно.

B. Сразу зафиксируй политику (канон 2026.7: `tools.exec.mode`):

```
openclaw config set tools.exec.mode allowlist
```

`mode=allowlist` = security=allowlist + ask=off. Не `full`. Не `ask`. Не `ask=on-miss`.

C. Allowlist агента main (постоянный). Только эти бинарники:

`ls cat head tail df journalctl date uname free zramctl mkdir mv tar gpg git ss curl openclaw`

Не в allowlist (и не добавляй сам): `rm reboot shutdown poweroff dd mkfs ufw iptables passwd chmod chown systemctl loginctl bash sh python3 node npm`.

D. На ЭТОТ прогон временно добавь в allowlist ещё `systemctl` и `loginctl`. После шагов 1–4 — СРАЗУ выкинь их из allowlist. В финальном отчёте allowlist без них.

E. Выключи telegram execApprovals, чтобы кнопки /approve больше не появлялись:

```
openclaw config set channels.telegram.execApprovals.enabled false
```

F. Host-файл `~/.openclaw/exec-approvals.json` (если есть): defaults.security=allowlist, defaults.ask=off, defaults.askFallback=deny. Агенту main то же. Не security=full.

G. iPhone node не трогай (camera.snap как было; sms/contacts/callLog deny).

H. Проверка: `openclaw config get tools.exec` — mode=allowlist. Попытка `uname -a` должна пройти без кнопки. Попытка `systemctl` после очистки allowlist — deny, без зависания.

---

## 1) git pull workspace

```
git -C /root/openclaw pull --ff-only origin main
```

Нужны файлы:
- `services/openclaw-gateway.service`
- `services/loop-watchdog.sh`
- `services/loop-watchdog-cron.sh`
- этот промпт

---

## 2) Gateway: user → system

Сначала прочитай живой user-юнит:

```
systemctl --user cat openclaw-gateway.service
```

Скопируй **точный ExecStart** (и Environment/PATH, если nvm) в `/etc/systemd/system/openclaw-gateway.service`. Шаблон — `services/openclaw-gateway.service`. Обязательно:

- Restart=on-failure, RestartSec=5, StartLimitBurst=5, StartLimitIntervalSec=120
- WantedBy=multi-user.target
- Environment=OPENCLAW_SERVICE_REPAIR_POLICY=external
- порт 18789, bind как сейчас (loopback). Не публиковать 18789.

Дальше, без простоя дольше минуты:

```
loginctl enable-linger root
export XDG_RUNTIME_DIR=/run/user/0
systemctl --user stop openclaw-gateway.service
systemctl --user disable openclaw-gateway.service
systemctl --user reset-failed openclaw-gateway.service || true
# убери user-файл, чтобы doctor не поднял двойник
# (~/.config/systemd/user/openclaw-gateway.service)
systemctl daemon-reload
systemctl enable --now openclaw-gateway.service
```

Проверки:
- `systemctl is-active openclaw-gateway` = active (без --user)
- `systemctl --user is-active openclaw-gateway` = inactive/not-found
- `ss -lptn | grep 18789` = 127.0.0.1:18789
- Telegram-бот отвечает на «пинг»
- `openclaw doctor` не должен заново ставить user-юнит (policy=external)

Не рестартуй r2d2-hub, если упал только gateway.

---

## 3) Watchdog :18789 и :8765

Поставь cron (тот же root crontab, что hub-watchdog), каждую минуту:

```
* * * * * /bin/sh /root/openclaw/services/loop-watchdog-cron.sh >/dev/null 2>&1
```

Скрипт уже читает `/root/atlas-green-pearl-dawn/.env` (HubAlertsbot). Не клади токен в crontab.

Правила скрипта (не переписывай логику):
- 3 провала подряд по каждому порту отдельно → restart только этого сервиса
- gateway: `systemctl restart openclaw-gateway` (после перевода на system)
- tgsvc: `systemctl restart telegram-user-svc`
- антишторм алертов **60 сек**
- r2d2-hub / ufw / zram не трогает
- хаб-watchdog не меняй

Проверка без шторма: `sh /root/openclaw/services/loop-watchdog-cron.sh` — оба порта ok, в Telegram ничего.

---

## 4) Модели — выжечь Google из LLM/vision

Хозяин утвердил (зафиксируй в конфиге, не в MEMORY с ключами):

- чат / heartbeat: deepseek/deepseek-v4-flash
- глубоко разобраться: deepseek/deepseek-v4-pro
- фото / разбор картинки: deepseek/deepseek-v4-flash-vision-exp
- генерация картинок: OpenRouter → Gemini Flash image

Сделай:
- primary/fallback/imageModel для чата и vision — DeepSeek, не Google, не gemini-* как LLM
- Google как LLM/vision/fallback — вырезать. Календарь хаба (gcal) НЕ трогать.
- imageGenerationModel можно оставить OpenRouter Gemini Flash (это генерация, не разбор входящих фото)
- plugins google для LLM не использовать как маршрутизатор картинок
- **не** звать CLI media / `openclaw media` для входящих фото
- не дай `openclaw doctor` или себе вернуть google в image-tool

Проверка: `openclaw config get` по ключам models / agents.defaults.model / image / vision / fallback — в отчёте имена моделей, не ключи. Входящее фото не должно уехать во Франкфурт-Google.

---

## 5) Документы workspace

Обнови (без секретов): `STATE.md`, `memory/profile.md`, `memory/2026-08-27.md`, `memory/playbooks.md`.
Зафиксируй: gateway = system-юнит; exec.mode=allowlist; апрувов нет; watchdog loop :18789+:8765; модели как выше.

`git add` только эти файлы. `git commit` / `git push` origin main. Не аддь `.env`, credentials, openclaw.json.

---

## Нельзя

- код хаба (`/root/atlas-green-pearl-dawn` src/)
- ufw, zram, swapfile
- Parallel / Context7 / GitHub MCP
- агент hub: tools.allow должен остаться []
- Mini App / :8080 / BotFather Mini App
- security=full, ask=on-miss, ask=always
- rm / reboot / chmod / chown как «починка»
- печатать токены

---

## Отчёт хозяину (короткий список)

- exec.mode / ask / telegram.execApprovals.enabled
- финальный allowlist (должен быть без systemctl)
- gateway: system active? user disabled? ss :18789
- linger root: yes/no
- cron loop-watchdog: строка есть?
- `uname -a` без апрува: ok?
- модели: chat / vision / image-gen (имена)
- google в llm/vision/fallback: нет?
- git push workspace: sha
- что не вышло
