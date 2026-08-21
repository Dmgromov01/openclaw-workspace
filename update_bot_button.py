import asyncio
import os
import re
from aiogram import Bot
from aiogram.types import MenuButtonWebApp, WebAppInfo

MINIAPP_URL = "https://gbkz.uk/miniapp/"

def get_token():
    # 1. Проверяем переменную окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    if token:
        return token
    # 2. Ищем токен в файле .env
    env_path = "/root/openclaw/.env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("TELEGRAM_BOT_TOKEN=") or line.startswith("BOT_TOKEN="):
                    return line.strip().split("=", 1)[1].strip(' "\'')
    # 3. Ищем в config.json или конфигах openclaw
    for cfg in ["/root/openclaw/config.json", "/root/.openclaw/config.json"]:
        if os.path.exists(cfg):
            with open(cfg, "r", encoding="utf-8") as f:
                content = f.read()
                m = re.search(r'["\']?(?:bot_token|token)["\']?\s*:\s*["\']([0-9]{8,10}:[a-zA-Z0-9_-]{35})["\']', content)
                if m:
                    return m.group(1)
    return None

async def main():
    try:
        token = get_token()
        if not token:
            print("Ошибка: Токен бота не найден. Задайте TELEGRAM_BOT_TOKEN или BOT_TOKEN в переменной окружения, .env или config.json.")
            return
        bot = Bot(token=token)
    except Exception as e:
        print(f"Ошибка при загрузке токена или создании бота: {e}")
        return

    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="⚡ OpenClaw Hub",
                web_app=WebAppInfo(url=MINIAPP_URL)
            )
        )
        print(f"Кнопка меню бота успешно привязана к: {MINIAPP_URL}")
    except Exception as e:
        print(f"Ошибка при установке кнопки: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
