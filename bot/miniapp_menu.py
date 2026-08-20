import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import MenuButtonWebApp, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Укажите ваш рабочий HTTPS-URL (Cloudflare Tunnel, ngrok или домен)
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://app.yourdomain.com")

async def setup_miniapp_button(bot: Bot):
    """Устанавливает кнопку WebApp слева от поля ввода текста в Telegram."""
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Personal Hub",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    )

def get_miniapp_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-кнопка для открытия дашборда из сообщений."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Открыть Personal Hub", web_app=WebAppInfo(url=MINIAPP_URL))]
    ])

async def start_cmd_handler(message: types.Message):
    """Ответ на команду /start с приветствием и инлайн-кнопкой."""
    await message.answer(
        f"Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "Ваш персональный дашборд доступен по кнопке меню слева или по кнопке ниже.",
        reply_markup=get_miniapp_keyboard(),
        parse_mode="HTML"
    )
