import os
import re
import json
import sqlite3
import asyncio
import logging
import subprocess
from datetime import datetime
from typing import Tuple, Optional

import aiohttp
import trafilatura
from pypdf import PdfReader
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from google import genai
from sqlalchemy import String, Text, DateTime, select, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

import sys
sys.path.append("/root/openclaw/calendar")
sys.path.append("/root/openclaw/services/assistant_bot")

try:
    from image_gen import generate_image
except ImportError:
    generate_image = None

try:
    from ai_image_editor import process_ai_photo
except ImportError:
    process_ai_photo = None

try:
    from caldav_client import add_event_to_calendar
except ImportError:
    add_event_to_calendar = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("assistant_bot")

# --- КОНФИГУРАЦИЯ И СЕКРЕТЫ ---

def get_secret(key_name: str, fallback: str = "") -> str:
    if os.environ.get(key_name):
        return os.environ[key_name].strip()
    
    # 1. Поиск в /etc/openclaw/secrets.json
    secrets_path = "/etc/openclaw/secrets.json"
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path) as f:
                data = json.load(f)
                if key_name in data:
                    return data[key_name].strip()
        except Exception:
            pass
            
    # 2. Поиск в credentials
    cred_file = f"/root/.openclaw/credentials/{key_name.lower().replace('_key', '')}.key"
    if os.path.exists(cred_file):
        try:
            return open(cred_file).read().strip()
        except Exception:
            pass
            
    return fallback

GEMINI_API_KEY = get_secret("ai-studio", os.environ.get("GOOGLE_API_KEY", ""))
DEEPSEEK_API_KEY = get_secret("deepseek_key", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "REDACTED-TELEGRAM-TOKEN")

VOICE_DIR = "/root/openclaw/workspace/media/voice"
PHOTO_DIR = "/root/openclaw/workspace/media/photos"
DOCS_DIR = "/root/openclaw/workspace/media/docs"
OUTBOX_DIR = "/root/openclaw/workspace/media/outbox"
DB_PATH = "/root/openclaw/data/app.db"
URL_REGEX = re.compile(r"https?://[^\s]+")

# --- БАЗА ДАННЫХ (SQLAlchemy 2.0 Async + SQLite WAL) ---

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

# --- ИНИЦИАЛИЗАЦИЯ КЛИЕНТОВ ---

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- ВСПОМОГАТЕЛЬНЫЕ AI-ФУНКЦИИ ---

def sync_to_ai_memory(category: str, text_content: str):
    """Запись оперативного контекста в подневной файл архива (memory/YYYY-MM-DD.md)."""
    try:
        mem_dir = "/root/openclaw/memory"
        os.makedirs(mem_dir, exist_ok=True)
        today_file = os.path.join(mem_dir, f"{datetime.now().strftime('%Y-%m-%d')}.md")
        now_time = datetime.now().strftime("%H:%M")
        
        entry = f"- [{now_time}] **{category}**: {text_content}
"
        with open(today_file, "a", encoding="utf-8") as f:
            f.write(entry)
        logger.info(f"Записано в подневной журнал {today_file}")
    except Exception as e:
        logger.warning(f"Ошибка записи в memory дневник: {e}")
async def process_llm_request(prompt: str) -> str:
    """Вызов DeepSeek с авто-фоллбэком на Gemini 3.6 Flash."""
    key = get_secret("deepseek_key", DEEPSEEK_API_KEY)
    if key and key.startswith("sk-"):
        try:
            url = "https://api.deepseek.com/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Ты лаконичный бизнес-ассистент. Отвечай строго по сути, сохраняя факты, условия и цифры."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=25) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"].strip()
                    err = await resp.text()
                    logger.warning(f"DeepSeek вернул ошибку ({resp.status}): {err}")
        except Exception as e:
            logger.warning(f"Ошибка запроса DeepSeek: {e}")

    # Fallback to Gemini 3.6 Flash
    try:
        resp = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model="gemini-3.6-flash",
            contents=[prompt]
        )
        return (resp.text or "").strip()
    except Exception as e:
        logger.error(f"Ошибка Gemini Fallback: {e}")
        return ""

# --- ОБРАБОТЧИКИ СООБЩЕНИЙ ---

@dp.message(Command("find"))
@dp.message(Command("search"))
async def handle_search(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Укажите запрос для поиска. Пример:\n`/find титан`")
        return
    query = parts[1].strip()

    def db_search(q: str):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        results = []
        try:
            cur.execute("SELECT title, summary FROM articles_fts WHERE articles_fts MATCH ? LIMIT 2", (q,))
            for r in cur.fetchall():
                results.append(f"📰 *Статья:* {r[0]}\n{r[1][:220]}...")
            
            cur.execute("SELECT action_item, transcript FROM voice_fts WHERE voice_fts MATCH ? LIMIT 2", (q,))
            for r in cur.fetchall():
                results.append(f"🗣 *Заметка:* {r[0]}\n_{r[1][:160]}..._")
        except Exception as e:
            logger.error(f"FTS search error: {e}")
        finally:
            conn.close()
        return results

    res = await asyncio.to_thread(db_search, query)
    if not res:
        await message.reply(f"🔍 По запросу `{query}` в локальной базе ничего не найдено.")
        return

    out = f"🔍 *Найдено в базе ({query}):*\n\n" + "\n\n---\n\n".join(res)
    await message.reply(out)

@dp.message(Command("draw"))
@dp.message(F.text.lower().startswith("нарисуй"))
async def handle_draw(message: Message):
    text = message.text or ""
    prompt = text[5:].strip() if text.startswith("/draw") else (text[7:].strip() if text.lower().startswith("нарисуй") else "")
    if not prompt:
        await message.reply("Укажите описание арта. Пример:\n`/draw спорткар на закате`")
        return

    status_msg = await message.reply("🎨 Генерирую изображение через Flux...")
    try:
        try:
            en_prompt = await process_llm_request(f"Translate this image prompt to concise descriptive English: {prompt}")
        except Exception:
            en_prompt = prompt

        loop = asyncio.get_running_loop()
        image_path = await loop.run_in_executor(None, generate_image, en_prompt)

        photo = FSInputFile(image_path)
        await message.reply_photo(photo=photo, caption=f"✨ **{prompt}**")
        await status_msg.delete()
    except Exception as e:
        logger.error(f"Error drawing image: {e}")
        await status_msg.edit_text("❌ Ошибка при генерации.")

@dp.message(F.photo)
async def handle_photo(message: Message):
    user_instruction = message.caption or ""
    status_text = "🪄 Выполняю AI-рестайлинг..." if user_instruction else "📸 Применяю студийную коррекцию..."
    status_msg = await message.reply(status_text)
    
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)

        os.makedirs(PHOTO_DIR, exist_ok=True)
        os.makedirs(OUTBOX_DIR, exist_ok=True)

        raw_path = os.path.join(PHOTO_DIR, f"raw_{photo.file_id}.jpg")
        ai_out_path = os.path.join(OUTBOX_DIR, f"ai_{photo.file_id}.jpg")

        await bot.download_file(file_info.file_path, raw_path)

        en_instruction = ""
        if user_instruction:
            try:
                en_instruction = await process_llm_request(f"Translate this photo instruction to concise English: {user_instruction}")
            except Exception:
                en_instruction = user_instruction

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, process_ai_photo, raw_path, ai_out_path, en_instruction)

        enhanced_file = FSInputFile(ai_out_path)
        await message.reply_photo(photo=enhanced_file, caption=f"✨ **Готово!**\n_{user_instruction or 'Студийный свет'}_")
        await status_msg.delete()

        if os.path.exists(raw_path): os.remove(raw_path)
        if os.path.exists(ai_out_path): os.remove(ai_out_path)
    except Exception as e:
        logger.error(f"Error AI photo refiner: {e}")
        await status_msg.edit_text("❌ Ошибка обработки фото.")

@dp.message(F.document)
async def handle_document(message: Message):
    doc = message.document
    if not (doc.file_name.endswith(".pdf") or doc.file_name.endswith(".txt")):
        return

    status_msg = await message.reply("📄 Извлекаю суть документа...")
    try:
        os.makedirs(DOCS_DIR, exist_ok=True)
        file_info = await bot.get_file(doc.file_id)
        local_path = os.path.join(DOCS_DIR, doc.file_name)
        await bot.download_file(file_info.file_path, local_path)

        text_content = ""
        if doc.file_name.endswith(".pdf"):
            reader = PdfReader(local_path)
            for page in reader.pages[:10]:
                text_content += page.extract_text() or ""
        else:
            with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read()

        prompt = (
            f"Сделай емкую аналитическую выжимку документа '{doc.file_name}':\n"
            f"- Главная суть\n- Ключевые условия, метрики и цифры\n- Итоговый вывод\n\n"
            f"Текст:\n{text_content[:8000]}"
        )
        summary = await process_llm_request(prompt)
        await status_msg.edit_text(f"📊 *Анализ документа {doc.file_name}:*\n\n{summary}")

        if os.path.exists(local_path): os.remove(local_path)
    except Exception as e:
        logger.error(f"Error reading document: {e}")
        await status_msg.edit_text("❌ Ошибка при разборе документа.")

async def summarize_url(url: str) -> str:
    async with AsyncSessionLocal() as session:
        cached = await session.scalar(select(SavedArticle).where(SavedArticle.url == url))
        if cached:
            return f"📌 (Из кэша)\n\n{cached.summary}"

    downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
    if not downloaded:
        return "❌ Не удалось загрузить страницу."

    text = await asyncio.to_thread(trafilatura.extract, downloaded, include_links=False, include_images=False)
    if not text or len(text.strip()) < 100:
        return "❌ Не удалось извлечь текст статьи."

    prompt = f"Сделай структурированное саммари статьи:\n- 3-5 ключевых тезисов\n- Главный вывод\n\nТекст:\n{text[:6000]}"
    summary = await process_llm_request(prompt)

    async with AsyncSessionLocal() as session:
        article = SavedArticle(url=url, title=url[:100], summary=summary)
        session.add(article)
        await session.commit()

    asyncio.create_task(asyncio.to_thread(sync_to_ai_memory, "read_articles", f"Статья {url}: {summary}"))
    return summary

@dp.message(F.text.regexp(URL_REGEX))
async def handle_url(message: Message):
    urls = URL_REGEX.findall(message.text)
    if not urls:
        return
    processing_msg = await message.reply("⏳ Извлекаю суть статьи...")
    try:
        summary = await summarize_url(urls[0])
        await processing_msg.edit_text(f"📰 **Выжимка:**\n\n{summary}")
    except Exception as e:
        logger.error(f"Error URL: {e}")
        await processing_msg.edit_text("❌ Ошибка при разборе ссылки.")

async def process_voice(ogg_path: str) -> Tuple[str, str, bool]:
    mp3_path = ogg_path.replace(".ogg", ".mp3")
    os.system(f"ffmpeg -y -i {ogg_path} -vn -ar 16000 -ac 1 -b:a 32k {mp3_path} >/dev/null 2>&1")
    
    target_path = mp3_path if os.path.exists(mp3_path) else ogg_path
    mime_type = "audio/mp3" if target_path.endswith(".mp3") else "audio/ogg"

    with open(target_path, "rb") as f:
        audio_bytes = f.read()

    gemini_prompt = "Сделай точную транскрипцию аудиозаписи на русском языке. Верни только текст."
    gemini_resp = await asyncio.to_thread(
        gemini_client.models.generate_content,
        model="gemini-3.6-flash",
        contents=[
            genai.types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            gemini_prompt
        ]
    )
    transcript = (gemini_resp.text or "").strip()

    prompt = (
        f"Текущая дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}.\n"
        f"Текст транскрипта: '{transcript}'\n\n"
        f"Ответь строго JSON-объектом без лишних символов:\n"
        f"{{\n"
        f'  "action_item": "Краткая суть или задача",\n'
        f'  "is_calendar_event": false,\n'
        f'  "event_title": "Название события",\n'
        f'  "event_datetime": "YYYY-MM-DD HH:MM"\n'
        f"}}"
    )
    res_raw = await process_llm_request(prompt)
    is_saved_to_cal = False
    try:
        clean_json = re.search(r"\{.*\}", res_raw, re.DOTALL)
        if clean_json:
            data = json.loads(clean_json.group(0))
            action_item = data.get("action_item", transcript)
            if data.get("is_calendar_event") and data.get("event_datetime") and add_event_to_calendar:
                dt_obj = datetime.strptime(data["event_datetime"], "%Y-%m-%d %H:%M")
                is_saved_to_cal = await asyncio.to_thread(
                    add_event_to_calendar, data.get("event_title", action_item), dt_obj, 60, transcript
                )
        else:
            action_item = res_raw
    except Exception:
        action_item = res_raw

    async with AsyncSessionLocal() as session:
        session.add(VoiceNote(transcript=transcript, action_item=action_item))
        await session.commit()

    asyncio.create_task(asyncio.to_thread(sync_to_ai_memory, "voice_tasks", f"Заметка: {action_item}"))

    if os.path.exists(ogg_path): os.remove(ogg_path)
    if os.path.exists(mp3_path): os.remove(mp3_path)
    return transcript, action_item, is_saved_to_cal

@dp.message(F.voice)
async def handle_voice(message: Message):
    file = await bot.get_file(message.voice.file_id)
    os.makedirs(VOICE_DIR, exist_ok=True)
    local_ogg = os.path.join(VOICE_DIR, f"{message.voice.file_id}.ogg")
    await bot.download_file(file.file_path, local_ogg)
    
    status = await message.reply("🎙 Распознаю...")
    try:
        transcript, action, cal_saved = await process_voice(local_ogg)
        cal_tag = "\n📅 *Событие добавлено в календарь!*" if cal_saved else ""
        await status.edit_text(f"🗣 **Текст:**\n{transcript}\n\n🎯 **Суть:**\n{action}{cal_tag}")
    except Exception as e:
        logger.error(f"Error Voice: {e}")
        await status.edit_text("❌ Ошибка при обработке голосового сообщения.")

async def main():
    logger.info("Assistant Bot запущен в оптимизированном режиме...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
