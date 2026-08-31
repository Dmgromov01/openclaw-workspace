# Установка R2D2 Hub

- Репо: /root/atlas-green-pearl-dawn, main.
- Сервис: r2d2-hub → .output/server/index.mjs, 127.0.0.1:8091.
- Снаружи: https://hub.gbkz.uk через nginx.
- Auth: Face ID + PIN + одноразовый инвайт; UI calendar: Google OAuth.
- Чат: hub:<userId>, tool_choice none, агент hub tools.allow=[].

## Обновление
1. Проверить git status, systemd, /healthz и /readyz.
2. Перед checkout/systemd сохранить backup.
3. При available RAM ≥400 MiB: npm ci, npm run typecheck, npm test, npm run build.
4. После успешной сборки: systemctl restart r2d2-hub.
5. Проверить /, /healthz, /readyz локально и публично.

## Не делать
Не возвращать Python Mini App, miniapp.service, :8080, Telegram HMAC/initData, /miniapp/, vite preview, Vercel или второй gateway. Не менять Face ID/PIN/инвайт, PGLite, hub:<userId>, tool_choice none и tools.allow=[].
