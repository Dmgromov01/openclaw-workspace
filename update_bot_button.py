import asyncio
import os
from aiogram import Bot
from aiogram.types import MenuButtonWebApp, WebAppInfo

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "REDACTED-TELEGRAM-TOKEN")
MINIAPP_URL = "https://equipment-rrp-states-awesome.trycloudflare.com"

async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="⚡ Personal Hub",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    )
    print(f"Кнопка меню бота успешно обновлена на: {MINIAPP_URL}")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
