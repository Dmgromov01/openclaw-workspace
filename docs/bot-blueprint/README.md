# OpenClaw Bot Blueprint — сборка ассистента с Jina-инструментами

Слепок идей. Живой плагин — [`plugins/jina-tools`](../../plugins/jina-tools), не копия в этой папке.
Модель/провайдер — на твой выбор. Канон инфраструктуры — [`STATE.md`](../../STATE.md).

Проверено на: OpenClaw 2026.7.1-2, Ubuntu 24.04, Node 22, 2GB RAM VPS.

---

## 1. Архитектура (что и зачем)

```
┌────────────────────────────────────────────────┐
│  OpenClaw Gateway (systemd: openclaw-gateway)  │
│  - Telegram-канал (бот)                        │
│  - Плагины: jina-tools (search + rag)          │
│  - memorySearch (гибрид vector+text)           │
│  - Модель: <твой провайдер>                    │
├────────────────────────────────────────────────┤
│  Плагин jina-tools (JS, SDK OpenClaw):         │
│   ├─ jina_search: веб-поиск + контент (markdown)│
│   └─ jina_rag: RAG по файлам (embeddings+rerank)│
├────────────────────────────────────────────────┤
│  Ключи: /root/.openclaw/credentials/*.key (600) │
│  Кэш RAG: /root/.openclaw/cache/jina_rag.json   │
└────────────────────────────────────────────────┘
```

### Слои
- **Gateway** — оркестрация, сессии, каналы, память. Ничего не трогаем в ядре.
- **Плагины** — официальный SDK (`definePluginEntry` + `api.registerTool`), контракты в манифесте.
- **Сервисы** — только то, что должно жить вне гейтвея (у тебя может быть ноль).
- **Хранилище** — credentials (600, вне git), cache (вне git), workspace в git.

---

## 2. Установка OpenClaw (Ubuntu 24.04)

```bash
# Node 22+
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs

# OpenClaw (npm global)
npm install -g openclaw

# Проверка
openclaw --version   # 2026.7.x
```

---

## 3. Конфиг: openclaw.example.json

Скопируй в `/root/.openclaw/openclaw.json`, замени плейсхолдеры:

```json
{
  "agents": {
    "defaults": {
      "workspace": "/root/openclaw",
      "model": {
        "primary": "<provider>/<model>",
        "fallbacks": ["<provider>/<fallback-model>"]
      },
      "memorySearch": {
        "enabled": true,
        "provider": "openai-compatible",
        "model": "openai/text-embedding-3-small",
        "remote": {
          "baseUrl": "https://openrouter.ai/api/v1",
          "apiKey": "<OPENROUTER_KEY>"
        },
        "query": {
          "maxResults": 6,
          "minScore": 0.35,
          "hybrid": {
            "enabled": true,
            "vectorWeight": 0.7,
            "textWeight": 0.3,
            "candidateMultiplier": 4
          }
        },
        "sources": ["memory", "sessions"]
      },
      "compaction": {
        "mode": "safeguard",
        "reserveTokens": 450000,
        "reserveTokensFloor": 100000,
        "keepRecentTokens": 200000,
        "truncateAfterCompaction": true
      }
    }
  },
  "gateway": {
    "mode": "local",
    "auth": { "mode": "token", "token": "<GENERATE_STRONG_TOKEN>" },
    "port": 18789,
    "bind": "loopback"
  },
  "session": { "dmScope": "per-channel-peer" },
  "tools": {
    "profile": "coding",
    "web": { "search": { "provider": "parallel-free", "maxResults": 5, "timeoutSeconds": 30 } }
  },
  "plugins": {
    "entries": {
      "jina-tools": { "enabled": true }
    },
    "load": { "paths": ["/root/openclaw/plugins/jina-tools"] },
    "allow": ["jina-tools", "telegram"],
    "bundledDiscovery": "compat"
  },
  "models": {
    "mode": "merge",
    "providers": {
      "<provider>": {
        "baseUrl": "<URL>",
        "api": "openai-completions",
        "apiKey": "<KEY>",
        "models": [
          {
            "id": "<model-id>",
            "name": "<Display Name>",
            "input": ["text"],
            "contextWindow": 200000,
            "maxTokens": 64000,
            "api": "openai-completions"
          }
        ]
      },
      "openrouter": {
        "baseUrl": "https://openrouter.ai/api/v1",
        "api": "openai-completions",
        "apiKey": "<OPENROUTER_KEY>",
        "models": [
          { "id": "openrouter/auto", "name": "OpenRouter Auto", "input": ["text"], "contextWindow": 200000, "maxTokens": 64000, "api": "openai-completions" },
          {
            "id": "openai/text-embedding-3-small",
            "name": "OpenAI Text Embedding 3 Small",
            "input": ["text"],
            "contextWindow": 8191,
            "maxTokens": 8191,
            "api": "openai-completions"
          }
        ]
      }
    }
  },
  "channels": {
    "telegram": {
      "botToken": "<BOT_TOKEN_FROM_BOTFATHER>",
      "enabled": true,
      "dmPolicy": "open",
      "allowFrom": ["*"]
    }
  },
  "skills": { "entries": {} }
}
```

### Важно про модели
- **memorySearch требует, чтобы embedding-модель была объявлена в каталоге провайдера.** Иначе векторная часть молча не работает (гибрид живёт на тексте 0.3). OpenRouter не показывает embedding-модели в GET /models, но POST /v1/embeddings работает.
- Провайдер для чата — любой (DeepSeek/OpenRouter/Gemini). Схема модели: `id`, `name`, `input:["text"]`, `contextWindow`, `maxTokens`, `api:"openai-completions"`.

---

## 4. Плагин jina-tools (код)

Полный код: каталог `plugins/jina-tools/` рядом с этим файлом (index.js, jina-core.js, openclaw.plugin.json, package.json).

Что делает:
- **jina_search** `<запрос>` — поиск через `https://s.jina.ai/?q=...`, возвращает markdown с контентом (до 15K символов). Резерв, когда встроенный web_search слаб.
- **jina_rag** `<запрос> [paths]` — семантический поиск по файлам: чанки (800 симв., overlap 100) → `jina-embeddings-v3` → топ-20 по косинусу → `jina-reranker-v2-base-multilingual` → топ-5. По умолчанию ищет по `MEMORY.md` + `memory/*.md`. Кэш векторов на диске (переиндексация только при изменении mtime файлов).

### Установка
```bash
mkdir -p /root/openclaw/plugins/jina-tools
# скопируй 4 файла из plugins/jina-tools/
mkdir -p /root/.openclaw/credentials
echo -n "<JINA_API_KEY>" > /root/.openclaw/credentials/jina.key
chmod 600 /root/.openclaw/credentials/jina.key
```

### Подводные камни Jina (проверено)
- **Rate limit: 100K токенов/мин** на тарифе. Индексация всей памяти (~60K токенов) упирается в лимит → в jina-core уже встроены: батчи по 20, паузы 2.5s, ретраи 20/40/60s на 429. Не уменьшай.
- Ключ — `Authorization: Bearer <key>`.
- Эндпоинты: search `https://s.jina.ai/`, embeddings `https://api.jina.ai/v1/embeddings` (model `jina-embeddings-v3`, task `text-matching`), rerank `https://api.jina.ai/v1/rerank` (model `jina-reranker-v2-base-multilingual`).

---

## 5. Безопасность (обязательный чек-лист — выстрадано)

1. **Файрвол**: ufw active, default deny incoming, open 22/80/443 (+tailnet 100.64.0.0/10 если нужно).
   ```bash
   ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
   ufw default deny incoming && ufw default allow outgoing
   ufw --force enable
   ```
2. **Bind**: gateway — только loopback (18789). Ничего публичного без nginx+TLS.
3. **Секреты**:
   - `/root/.openclaw/credentials/` — только там, chmod 600, НИКОГДА в git.
   - `.env` — не в git (добавь в .gitignore).
   - **Bot token**: если хоть раз попал в git-историю — ротация через @BotFather (/revoke), `git rm --cached` не лечит историю.
4. **.gitignore минимум**:
   ```
   .env
   .env.*
   *.key
   credentials/
   *.db
   *.sqlite
   node_modules/
   .venv/
   venv/
   cache/
   *.log
   *.log.*
   ```
5. **Никогда не коммить**: `.venv/` (сотни МБ), `*.db` (пароли/сессии/PII), логи.
6. **Таймауты в плагинах** — обязательны (`AbortSignal.timeout`), иначе зависший HTTP вешает агента.

---

## 6. Запуск

```bash
# systemd user unit
systemctl --user enable --now openclaw-gateway
openclaw gateway status

# Логи
journalctl --user -u openclaw-gateway -f

# iPhone/клиент: подключайся через setup code
openclaw qr --url wss://<host>:443
```

### Проверка после старта
- В логах: `http server listening (N plugins: ... jina-tools ...)` — плагин загружен.
- Спроси бота: «найди что-нибудь» (jina_search) и «что в памяти про X» (jina_rag).

---

## 7. Что сознательно НЕ включено (убери сам, если не нужно)

- miniapp / Telegram Mini App (отдельный Python-сервер, nginx, БД) — здесь нет.
- Дайджест/RSS/TG-каналы — здесь нет.
- Календарь (Google/iCloud) — здесь нет.
- tg-user-tools (личный Telegram через MTProto) — здесь нет (требует api_id/api_hash + сессию).
- Отчёты/аудит — это внутренняя история, не нужна.

---

## 8. Уроки, сэкономленные на граблях

- **Не поднимай второй гейтвей** (`--profile test`) пока работает прод — OpenClaw блокирует второй инстанс на том же хосте (guard).
- **Рестарт гейтвея прерывает сессию** — делай правки конфига файлом, потом `systemctl --user restart`.
- **keepRecentTokens держи завышенным** относительно пика диалога, иначе карусель overflow → already_compacted → фейл.
- **Логи растут** — ставь logrotate сразу (пример: /etc/logrotate.d, weekly×4, copytruncate).
- **healthcheck.sh** — свой smoke-тест (py_compile + сервисы + curl) и в cron; ловишь поломки до пользователя.
