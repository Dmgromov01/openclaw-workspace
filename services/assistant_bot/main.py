import os
import re
import json
import asyncio
import logging
from datetime import datetime
import aiohttp
import trafilatura
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from google import genai
from sqlalchemy import BigInteger, String, Text, DateTime, select, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Импортируем генератор изображений
import sys
sys.path.append("/root/openclaw/calendar")
try:
    from image_gen import generate_image
except ImportError:
    generate_image = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("assistant_bot")

def get_file_content(path: str, default: str = "") -> str:
    if os.path.exists(path):
        try:
            return open(path).read().strip()
        except Exception:
            return default
    return default

def get_deepseek_key() -> str:
    secrets_path = "/etc/openclaw/secrets.json"
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path) as f:
                data = json.load(f)
                return data.get("deepseek_key", "")
        except Exception:
            pass
    return os.environ.get("DEEPSEEK_API_KEY", "")

GEMINI_API_KEY = get_file_content("/root/.openclaw/credentials/ai-studio.key", os.environ.get("GOOGLE_API_KEY", ""))
DEEPSEEK_API_KEY = get_deepseek_key()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "REDACTED-TELEGRAM-TOKEN")

VOICE_DIR = "/root/openclaw/workspace/media/voice"
PHOTO_DIR = "/root/openclaw/workspace/media/photos"
DB_PATH = "/root/openclaw/data/app.db"
URL_REGEX = re.compile(r"https?://[^\s]+")

class Base(DeclarativeBase):
    pass

class SavedArticle(Base):
    __tablename__ = "saved_articles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(1024), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class VoiceNote(Base):
    __tablename__ = "voice_notes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transcript: Mapped[str] = mapped_column(Text)
    action_item: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=False)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

async def call_deepseek(prompt: str) -> str:
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты лаконичный бизнес-ассистент. Отвечай строго по сути, сохраняя факты и цифры, без вводных слов и воды."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload, timeout=45) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
            err = await resp.text()
            raise RuntimeError(f"DeepSeek API Error ({resp.status}): {err}")

# --- 1. ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ (Flux, Бесплатно) ---

@dp.message(Command("draw"))
@dp.message(F.text.lower().startswith("нарисуй"))
async def handle_draw(message: Message):
    text = message.text
    if text.startswith("/draw"):
        prompt = text[5:].strip()
    elif text.lower().startswith("нарисуй"):
        prompt = text[7:].strip()
    else:
        prompt = ""

    if not prompt:
        await message.reply("Укажите промпт для генерации. Пример:\n`/draw спорткар в неоновом городе`")
        return

    status_msg = await message.reply("🎨 Генерирую изображение через Flux...")

    try:
        # Перевод промпта на английский для лучшего качества генерации
        en_prompt_query = f"Translate this image generation prompt to concise English: {prompt}"
        try:
            en_prompt = await call_deepseek(en_prompt_query)
        except Exception:
            en_prompt = prompt

        loop = asyncio.get_running_loop()
        image_path = await loop.run_in_executor(None, generate_image, en_prompt)

        photo = FSInputFile(image_path)
        await message.reply_photo(photo=photo, caption=f"✨ **{prompt}**")
        await status_msg.delete()
    except Exception as e:
        logger.error(f"Error drawing image: {e}")
        await status_msg.edit_text("❌ Ошибка генерации изображения.")

# --- 2. АНАЛИЗ ФОТО И СКРИНШОТОВ (Gemini 2.5 Flash Vision, Бесплатно) ---

@dp.message(F.photo)
async def handle_photo(message: Message):
    status_msg = await message.reply("👁 Анализирую изображение...")
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)

        os.makedirs(PHOTO_DIR, exist_ok=True)
        local_path = os.path.join(PHOTO_DIR, f"{photo.file_id}.jpg")
        await bot.download_file(file_info.file_path, local_path)

        with open(local_path, "rb") as f:
            image_bytes = f.read()

        caption_text = message.caption or "Опиши подробно, что на фото, извлеки текст или выдели главное."
        prompt = (
            f"Пользователь прислал изображение с вопросом/комментарием: '{caption_text}'. "
            "Дай точный, структурированный и полезный ответ на русском языке."
        )

        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model="gemini-2.5-flash",
            contents=[
                genai.types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                prompt
            ]
        )

        if os.path.exists(local_path):
            os.remove(local_path)

        await status_msg.edit_text(response.text.strip())
    except Exception as e:
        logger.error(f"Error analyzing photo: {e}")
        await status_msg.edit_text("❌ Ошибка анализа изображения.")

# --- 3. САММАРИ СТАТЕЙ (DeepSeek) ---

async def summarize_url(url: str) -> str:
    async with AsyncSessionLocal() as session:
        cached = await session.scalar(select(SavedArticle).where(SavedArticle.url == url))
        if cached:
            return f"📌 (Из кэша)\n\n{cached.summary}"

    downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
    if not downloaded:
        return "❌ Не удалось загрузить страницу по ссылке."

    text = await asyncio.to_thread(trafilatura.extract, downloaded, include_links=False, include_images=False)
    if not text or len(text.strip()) < 100:
        return "❌ Не удалось извлечь текст статьи."

    prompt = (
        f"Сделай структурированное саммари статьи:\n"
        f"- 3-5 ключевых тезисов (списком)\n"
        f"- Главный вывод\n\n"
        f"Текст:\n{text[:6000]}"
    )
    summary = await call_deepseek(prompt)

    async with AsyncSessionLocal() as session:
        article = SavedArticle(url=url, title=url[:100], summary=summary)
        session.add(article)
        await session.commit()

    return summary

@dp.message(F.text.regexp(URL_REGEX))
async def handle_url(message: Message):
    urls = URL_REGEX.findall(message.text)
    if not urls:
        return
    url = urls[0]
    processing_msg = await message.reply("⏳ Извлекаю суть статьи...")
    try:
        summary = await summarize_url(url)
        await processing_msg.edit_text(f"📰 **Выжимка:**\n\n{summary}")
    except Exception as e:
        logger.error(f"Error URL: {e}")
        await processing_msg.edit_text("❌ Ошибка при обработке ссылки.")

# --- 4. ГОЛОСОВЫЕ СООБЩЕНИЯ (Gemini Audio -> DeepSeek) ---

async def process_voice(ogg_path: str) -> tuple[str, str]:
    mp3_path = ogg_path.replace(".ogg", ".mp3")
    cmd = f"ffmpeg -y -i {ogg_path} -vn -ar 16000 -ac 1 -b:a 32k {mp3_path} >/dev/null 2>&1"
    os.system(cmd)

    with open(mp3_path, "rb") as f:
        audio_bytes = f.read()

    gemini_prompt = "Сделай точную транскрипцию аудиозаписи на русском языке. Верни только текст."
    gemini_resp = await asyncio.to_thread(
        gemini_client.models.generate_content,
        model="gemini-2.5-flash",
        contents=[
            genai.types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3"),
            gemini_prompt
        ]
    )
    transcript = gemini_resp.text.strip()

    deepseek_prompt = (
        f"На основе транскрипции выдели главную суть или сформулируй конкретную задачу/чек-лист:\n\n"
        f"Текст: {transcript}"
    )
    action_item = await call_deepseek(deepseek_prompt)

    async with AsyncSessionLocal() as session:
        note = VoiceNote(transcript=transcript, action_item=action_item)
        session.add(note)
        await session.commit()

    if os.path.exists(ogg_path): os.remove(ogg_path)
    if os.path.exists(mp3_path): os.remove(mp3_path)

    return transcript, action_item

@dp.message(F.voice)
async def handle_voice(message: Message):
    voice = message.voice
    file_id = voice.file_id
    file = await bot.get_file(file_id)
    
    os.makedirs(VOICE_DIR, exist_ok=True)
    local_ogg = os.path.join(VOICE_DIR, f"{file_id}.ogg")

    await bot.download_file(file.file_path, local_ogg)
    processing_msg = await message.reply("🎙 Распознаю...")

    try:
        transcript, action = await process_voice(local_ogg)
        response_text = (
            f"🗣 **Текст:**\n{transcript}\n\n"
            f"🎯 **Суть / Задача:**\n{action}"
        )
        await processing_msg.edit_text(response_text)
    except Exception as e:
        logger.error(f"Error Voice: {e}")
        await processing_msg.edit_text("❌ Ошибка обработки голосового сообщения.")

# --- СТАРТ СЕРВИСА ---

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Assistant Bot запущен (Drawing + Vision + Voice + Summaries)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
